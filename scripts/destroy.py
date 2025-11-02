import subprocess
import os
import sys
import yaml
from typing import List, Tuple
import shutil

USAGE = (
    "Usage:\n"
    "  python scripts/destroy.py [--force] <yaml1.yaml> [yaml2.yaml ...]\n"
    "  python scripts/destroy.py [--force] --project <project_id> [--project <project_id> ...]\n"
    "Notes: Targets can be one or more YAML files and/or --project ids.\n"
)

def resolve_gcloud_bin() -> str:
    """Return path to gcloud binary or empty string if not found.

    Resolution order:
      1) GCLOUD_BIN env var (explicit path)
      2) PATH (shutil.which)
      3) Common Windows installs
    """
    # 1) Env var
    gcb = os.environ.get("GCLOUD_BIN", "").strip().strip('"')
    if gcb and os.path.exists(gcb):
        return gcb
    # 2) PATH
    found = shutil.which("gcloud")
    if found:
        return found
    # 3) Common Windows paths
    candidates = [
        r"C:\\Program Files\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd",
        r"C:\\Program Files\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.exe",
        r"C:\\Program Files (x86)\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd",
        r"C:\\Program Files (x86)\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""

def yaml_to_dict(yaml_file: str) -> dict:
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f) or {}

def get_project_id_from_yaml(yaml_path: str) -> str:
    data = yaml_to_dict(yaml_path)
    pid = data.get("project_id")
    if not pid:
        raise ValueError(f"project_id missing in YAML: {yaml_path}")
    return pid

def parse_args(argv: List[str]) -> Tuple[bool, List[str]]:
    auto_approve = False
    project_ids: List[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--force":
            auto_approve = True
            i += 1
            continue
        if arg.startswith("--project="):
            project_ids.append(arg.split("=", 1)[1])
            i += 1
            continue
        if arg == "--project":
            if i + 1 >= len(argv):
                raise ValueError("--project requires a value")
            project_ids.append(argv[i + 1])
            i += 2
            continue
        if arg.endswith((".yaml", ".yml")):
            if not os.path.exists(arg):
                raise FileNotFoundError(f"YAML not found: {arg}")
            project_ids.append(get_project_id_from_yaml(arg))
            i += 1
            continue
        raise ValueError(f"Unrecognized argument: {arg}\n\n{USAGE}")

    if not project_ids:
        raise ValueError(f"No targets provided.\n\n{USAGE}")

    # Deduplicate while preserving order
    seen = set()
    unique: List[str] = []
    for pid in project_ids:
        if pid not in seen:
            seen.add(pid)
            unique.append(pid)
    return auto_approve, unique

def run_destroy_for_project(project_id: str, auto_approve: bool) -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    run_dir = os.path.join(project_root, ".tf-runs", project_id)
    tfvars = os.path.join(run_dir, "terraform.tfvars.json")

    if not os.path.isdir(run_dir):
        raise FileNotFoundError(f"Run directory not found: {run_dir}. Deploy first.")
    if not os.path.exists(tfvars):
        raise FileNotFoundError(f"tfvars not found: {tfvars}. Deploy first.")

    cwd_before = os.getcwd()
    try:
        os.chdir(run_dir)
        print(f"[INFO] Destroying project '{project_id}' in: {run_dir}")

        def terraform_state_list() -> List[str]:
            try:
                out = subprocess.check_output(["terraform", "state", "list"], text=True)
                return [line.strip() for line in out.splitlines() if line.strip()]
            except subprocess.CalledProcessError:
                return []

        def destroy_targets(addresses: List[str]) -> None:
            if not addresses:
                return
            cmd = ["terraform", "destroy", "-var-file", tfvars]
            if auto_approve:
                cmd.append("-auto-approve")
            # add each target
            for addr in addresses:
                cmd.extend(["-target", addr])
            print(f"[INFO] Running targeted destroy for {len(addresses)} address(es)...")
            subprocess.run(cmd, check=True)

        # Phase 0: make sure we're initialized (in case of fresh shell)
        subprocess.run(["terraform", "init", "-input=false"], check=True)

        # Phase 1: Destroy compute instances first (to free subnets/networks)
        state_addrs = terraform_state_list()
        vm_addrs = [a for a in state_addrs if ".google_compute_instance." in a]
        if vm_addrs:
            print(f"[INFO] Found {len(vm_addrs)} compute instance(s) to destroy first")
            destroy_targets(vm_addrs)
        else:
            print("[INFO] No compute instances found in state; skipping targeted VM destroy")

        # Phase 2: Destroy other dependent items that commonly block networks
        state_addrs = terraform_state_list()
        blockers = []
        for needle in (
            ".google_compute_router.",
            ".google_compute_router_nat.",
            ".google_compute_firewall.",
            ".google_compute_forwarding_rule.",
            ".google_compute_address.",
        ):
            blockers.extend([a for a in state_addrs if needle in a])
        if blockers:
            print(f"[INFO] Destroying {len(blockers)} network-dependent resource(s) before full destroy")
            destroy_targets(blockers)

        # Phase 3: Full destroy, serialized to reduce race conditions
        full_cmd = [
            "terraform", "destroy",
            "-var-file", tfvars,
            "-parallelism=1",
        ]
        if auto_approve:
            full_cmd.append("-auto-approve")
        print(f"[INFO] Running: {' '.join(full_cmd)}")
        try:
            subprocess.run(full_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print("[WARN] Full destroy failed once. Waiting 10s and retrying once...")
            try:
                import time
                time.sleep(10)
            except Exception:
                pass
            subprocess.run(full_cmd, check=True)

        print(f"[INFO] ✅ Destroy completed for {project_id}")
    finally:
        os.chdir(cwd_before)

def main():
    print("=== Terraform Destroy Script ===")
    try:
        auto_approve, projects = parse_args(sys.argv[1:])
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if not auto_approve:
        confirm = input(f"This will destroy {len(projects)} project(s): {', '.join(projects)}. Proceed? (yes/no): ")
        if confirm.lower() not in ("yes", "y"):
            print("[INFO] Destroy cancelled.")
            sys.exit(0)

    try:
        for pid in projects:
            # Ask per-project what to do
            while True:
                print(f"\nChoose action for project '{pid}':")
                print("  [m] Delete modules/resources (Terraform destroy)")
                print("  [p] Delete entire project (also attempts gcloud project delete)")
                print("  [e] Exit")
                action = input("Enter choice [m/p/e]: ").strip().lower()
                if action in ("m", "p", "e"):
                    break

            if action == "e":
                print("[INFO] Exiting by user request.")
                sys.exit(0)

            # Always destroy modules/resources first
            run_destroy_for_project(pid, auto_approve)

            if action == "p":
                # Attempt to delete the project explicitly
                print(f"[INFO] Attempting to unlink billing and delete project '{pid}' via gcloud...")
                gcloud_bin = resolve_gcloud_bin()
                if not gcloud_bin:
                    print("[WARN] gcloud not found. Set GCLOUD_BIN env var or add Cloud SDK to PATH.")
                else:
                    try:
                        subprocess.run([gcloud_bin, "beta", "billing", "projects", "unlink", pid], check=False)
                    except Exception as e:
                        print(f"[WARN] Could not unlink billing for {pid}: {e}")
                    try:
                        subprocess.run([gcloud_bin, "projects", "delete", pid, "--quiet"], check=False)
                    except Exception as e:
                        print(f"[WARN] Could not delete project {pid}: {e}")

                # Remove run directory only if project is confirmed deleted or in delete-requested state
                try:
                    gcloud_bin = resolve_gcloud_bin()
                    check = subprocess.run(
                        [gcloud_bin if gcloud_bin else "gcloud", "projects", "describe", pid, "--format=value(lifecycleState)"],
                        capture_output=True, text=True
                    )
                    lifecycle = (check.stdout or "").strip()
                    if check.returncode != 0 or lifecycle == "DELETE_REQUESTED":
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        project_root = os.path.dirname(script_dir)
                        run_dir = os.path.join(project_root, ".tf-runs", pid)
                        import shutil
                        shutil.rmtree(run_dir, ignore_errors=True)
                        print(f"[INFO] Removed run directory: {run_dir}")
                    else:
                        print(f"[INFO] Project '{pid}' lifecycleState='{lifecycle}'. Keeping run directory.")
                except Exception as e:
                    print(f"[WARN] Could not verify project deletion for {pid}: {e}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Terraform destroy failed with exit code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
