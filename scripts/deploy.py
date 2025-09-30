#for usage cd to this location and python deploy.py ../configs/example-project.yaml
import yaml
import json
import subprocess
import sys
import os
from typing import List

def yaml_to_dict(yaml_file: str) -> dict:
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f)

def write_tfvars_json(data: dict, target_path: str) -> str:
    with open(target_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Wrote tfvars -> {target_path}")
    return target_path

def ensure_module_index(index: int) -> str:
    """Return module subdirectory name like 'project1'..'project12' cycling by index (1-based)."""
    module_num = ((index - 1) % 12) + 1
    return f"project{module_num}"

def write_minimal_root_tf(run_dir: str, module_source_rel: str) -> None:
    """Create minimal Terraform root files in run_dir that call the given module source path."""
    required = (
        "terraform {\n"
        "  required_providers {\n"
        "    google = {\n"
        "      source  = \"hashicorp/google\"\n"
        "      version = \"7.4.0\"\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        "provider \"google\" {\n"
        "  project = var.project_id\n"
        "}\n\n"
        f"module \"project\" {{\n"
        f"  source          = \"{module_source_rel}\"\n"
        f"  project_id      = var.project_id\n"
        f"  organization_id = var.organization_id\n"
        f"  billing_account = var.billing_account\n"
        f"  labels          = var.labels\n"
        f"  apis            = var.apis\n"
        f"}}\n"
    )

    variables = (
        "variable \"project_id\" {\n"
        "  description = \"The ID of the project\"\n"
        "  type        = string\n"
        "}\n\n"
        "variable \"organization_id\" {\n"
        "  description = \"Organization ID\"\n"
        "  type        = string\n"
        "  default     = null\n"
        "}\n\n"
        "variable \"billing_account\" {\n"
        "  description = \"Billing account ID\"\n"
        "  type        = string\n"
        "}\n\n"
        "variable \"labels\" {\n"
        "  description = \"Labels for the project\"\n"
        "  type        = map(string)\n"
        "  default     = {}\n"
        "}\n\n"
        "variable \"apis\" {\n"
        "  description = \"List of APIs to enable\"\n"
        "  type        = list(string)\n"
        "  default     = []\n"
        "}\n"
    )

    with open(os.path.join(run_dir, "main.tf"), "w", encoding="utf-8") as f:
        f.write(required)
    with open(os.path.join(run_dir, "variables.tf"), "w", encoding="utf-8") as f:
        f.write(variables)

def run_terraform_in_dir(run_dir: str, tfvars_path: str) -> None:
    cwd_before = os.getcwd()
    try:
        os.chdir(run_dir)
        print(f"[INFO] Running Terraform in: {run_dir}")
        subprocess.run(["terraform", "init"], check=True)
        subprocess.run([
            "terraform", "apply",
            "-var-file", tfvars_path,
            "-auto-approve"
        ], check=True)
    finally:
        os.chdir(cwd_before)

def normalize_inputs(argv: List[str]) -> List[str]:
    """Return a list of YAML file paths from argv (can include directories)."""
    result: List[str] = []
    for arg in argv:
        if os.path.isdir(arg):
            for name in os.listdir(arg):
                if name.endswith((".yaml", ".yml")):
                    result.append(os.path.join(arg, name))
        else:
            result.append(arg)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for p in result:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique

def main():
    # Determine input YAML files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    input_paths: List[str]
    if len(sys.argv) <= 1:
        input_paths = [os.path.join(project_root, "configs", "example-project.yaml")]
    else:
        input_paths = normalize_inputs(sys.argv[1:])

    # Validate inputs
    yaml_files: List[str] = []
    for p in input_paths:
        if not os.path.exists(p):
            print(f"[ERROR] File or directory not found: {p}")
            sys.exit(1)
        if os.path.isdir(p):
            continue
        if not p.endswith((".yaml", ".yml")):
            print(f"[WARN] Skipping non-YAML file: {p}")
            continue
        yaml_files.append(p)

    if not yaml_files:
        print("[ERROR] No YAML files provided.")
        sys.exit(1)

    runs_root = os.path.join(project_root, ".tf-runs")
    os.makedirs(runs_root, exist_ok=True)

    for idx, yaml_file in enumerate(yaml_files, start=1):
        print(f"\n=== Processing: {yaml_file} ===")
        data = yaml_to_dict(yaml_file)
        if not isinstance(data, dict):
            print(f"[ERROR] YAML file is empty or invalid: {yaml_file}")
            sys.exit(1)

        project_id = data.get("project_id")
        if not project_id:
            print(f"[ERROR] 'project_id' missing in {yaml_file}")
            sys.exit(1)

        run_dir = os.path.join(runs_root, project_id)
        os.makedirs(run_dir, exist_ok=True)

        # Decide which module to use (cycle 1..12)
        module_dir_name = ensure_module_index(idx)
        # module source relative path from run_dir to modules/<module_dir_name>
        module_source_rel = os.path.relpath(
            os.path.join(project_root, "modules", module_dir_name),
            start=run_dir,
        ).replace("\\", "/")

        # Write minimal root files for this run
        write_minimal_root_tf(run_dir, module_source_rel)

        # Write tfvars.json into run_dir
        tfvars_path = os.path.join(run_dir, "terraform.tfvars.json")
        write_tfvars_json(data, tfvars_path)

        # Execute terraform init/apply for this run
        run_terraform_in_dir(run_dir, tfvars_path)

if __name__ == "__main__":
    main()
