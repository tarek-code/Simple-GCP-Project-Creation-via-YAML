import subprocess
import os
import sys
import yaml
from typing import List, Tuple

USAGE = (
    "Usage:\n"
    "  python scripts/destroy.py [--force] <yaml1.yaml> [yaml2.yaml ...]\n"
    "  python scripts/destroy.py [--force] --project <project_id> [--project <project_id> ...]\n"
    "Notes: Targets can be one or more YAML files and/or --project ids.\n"
)

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
        cmd = [
            "terraform", "destroy",
            "-var-file", tfvars,
        ]
        if auto_approve:
            cmd.append("-auto-approve")
        print(f"[INFO] Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
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
            run_destroy_for_project(pid, auto_approve)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Terraform destroy failed with exit code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
