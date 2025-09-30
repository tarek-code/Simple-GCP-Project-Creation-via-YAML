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

def rel(from_dir: str, to_path: str) -> str:
    return os.path.relpath(to_path, start=from_dir).replace("\\", "/")

def write_minimal_root_tf(run_dir: str, module_source_rel: str) -> None:
    """Create minimal Terraform root files in run_dir that call the given module source path for project creation."""
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
        "variable \"resources\" {\n"
        "  description = \"Ignored placeholder to silence warnings when tfvars contains 'resources'\"\n"
        "  type        = any\n"
        "  default     = null\n"
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

def build_module_blocks(run_dir: str, project_root: str, data: dict) -> str:
    resources = data.get("resources", {}) or {}
    blocks: List[str] = []

    def mod_source(name: str) -> str:
        return rel(run_dir, os.path.join(project_root, "modules", name))

    # Storage buckets
    for i, b in enumerate(resources.get("storage_buckets", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"storage_bucket_{i}\" {{",
                f"  source  = \"{mod_source('storage_bucket')}\"",
                f"  project_id = var.project_id",
                f"  name        = \"{b['name']}\"",
                f"  location    = \"{b.get('location', 'US')}\"",
                f"  uniform_bucket_level_access = {str(b.get('uniform_bucket_level_access', True)).lower()}",
                f"  enable_versioning = {str(b.get('enable_versioning', False)).lower()}",
                f"  labels = {json.dumps(b.get('labels', {}))}",
                f"}}\n",
            ])
        )

    # VPC
    if vpc := resources.get("vpc"):
        blocks.append(
            "\n".join([
                f"module \"vpc\" {{",
                f"  source  = \"{mod_source('vpc')}\"",
                f"  project_id   = var.project_id",
                f"  name         = \"{vpc['name']}\"",
                f"  routing_mode = \"{vpc.get('routing_mode', 'GLOBAL')}\"",
                f"  description  = {json.dumps(vpc.get('description'))}",
                f"}}\n",
            ])
        )

    # Subnets
    for i, sn in enumerate(resources.get("subnets", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"subnet_{i}\" {{",
                f"  source  = \"{mod_source('subnet')}\"",
                f"  project_id     = var.project_id",
                f"  name           = \"{sn['name']}\"",
                f"  region         = \"{sn['region']}\"",
                f"  ip_cidr_range  = \"{sn['ip_cidr_range']}\"",
                f"  network        = \"{sn['network']}\"",
                f"  private_ip_google_access = {str(sn.get('private_ip_google_access', True)).lower()}",
                f"  purpose        = {json.dumps(sn.get('purpose'))}",
                f"}}\n",
            ])
        )

    # Firewall rules
    for i, fw in enumerate(resources.get("firewall_rules", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"firewall_{i}\" {{",
                f"  source  = \"{mod_source('firewall')}\"",
                f"  project_id = var.project_id",
                f"  name       = \"{fw['name']}\"",
                f"  network    = \"{fw['network']}\"",
                f"  direction  = \"{fw.get('direction', 'INGRESS')}\"",
                f"  priority   = {int(fw.get('priority', 1000))}",
                f"  protocol   = \"{fw.get('protocol', 'tcp')}\"",
                f"  ports      = {json.dumps(fw.get('ports', ['22']))}",
                f"  source_ranges = {json.dumps(fw.get('source_ranges', ['0.0.0.0/0']))}",
                f"  target_tags   = {json.dumps(fw.get('target_tags', []))}",
                f"}}\n",
            ])
        )

    # Service accounts
    for i, sa in enumerate(resources.get("service_accounts", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"service_account_{i}\" {{",
                f"  source  = \"{mod_source('service_account')}\"",
                f"  project_id   = var.project_id",
                f"  account_id   = \"{sa['account_id']}\"",
                f"  display_name = {json.dumps(sa.get('display_name'))}",
                f"  description  = {json.dumps(sa.get('description'))}",
                f"}}\n",
            ])
        )

    # IAM bindings
    for i, ib in enumerate(resources.get("iam_bindings", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"iam_binding_{i}\" {{",
                f"  source  = \"{mod_source('iam_binding')}\"",
                f"  project_id = var.project_id",
                f"  role    = \"{ib['role']}\"",
                f"  member  = \"{ib['member']}\"",
                f"}}\n",
            ])
        )

    # Pub/Sub topics
    for i, pt in enumerate(resources.get("pubsub_topics", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"pubsub_topic_{i}\" {{",
                f"  source  = \"{mod_source('pubsub')}\"",
                f"  project_id = var.project_id",
                f"  name    = \"{pt['name']}\"",
                f"  labels  = {json.dumps(pt.get('labels', {}))}",
                f"}}\n",
            ])
        )

    # Cloud Run
    for i, cr in enumerate(resources.get("cloud_run_services", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"cloud_run_{i}\" {{",
                f"  source   = \"{mod_source('cloud_run')}\"",
                f"  project_id = var.project_id",
                f"  name     = \"{cr['name']}\"",
                f"  location = \"{cr.get('location', 'us-central1')}\"",
                f"  image    = \"{cr['image']}\"",
                f"}}\n",
            ])
        )

    # Cloud SQL
    for i, cs in enumerate(resources.get("cloud_sql_instances", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"cloud_sql_{i}\" {{",
                f"  source   = \"{mod_source('cloud_sql')}\"",
                f"  project_id = var.project_id",
                f"  name             = \"{cs['name']}\"",
                f"  database_version = \"{cs.get('database_version', 'POSTGRES_14')}\"",
                f"  region           = \"{cs.get('region', 'us-central1')}\"",
                f"  tier             = \"{cs.get('tier', 'db-f1-micro')}\"",
                f"}}\n",
            ])
        )

    # Artifact Registry
    for i, ar in enumerate(resources.get("artifact_repos", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"artifact_registry_{i}\" {{",
                f"  source   = \"{mod_source('artifact_registry')}\"",
                f"  project_id = var.project_id",
                f"  name      = \"{ar['name']}\"",
                f"  location  = \"{ar.get('location', 'us')}\"",
                f"  format    = \"{ar.get('format', 'DOCKER')}\"",
                f"  description = {json.dumps(ar.get('description'))}",
                f"}}\n",
            ])
        )

    # Secret Manager
    for i, sm in enumerate(resources.get("secrets", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"secret_{i}\" {{",
                f"  source   = \"{mod_source('secret_manager')}\"",
                f"  project_id = var.project_id",
                f"  name    = \"{sm['name']}\"",
                f"  value   = {json.dumps(sm.get('value', ''))}",
                f"}}\n",
            ])
        )

    # Cloud DNS
    for i, dz in enumerate(resources.get("dns_zones", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"dns_zone_{i}\" {{",
                f"  source   = \"{mod_source('cloud_dns')}\"",
                f"  project_id = var.project_id",
                f"  name     = \"{dz['name']}\"",
                f"  dns_name = \"{dz['dns_name']}\"",
                f"  description = {json.dumps(dz.get('description'))}",
                f"}}\n",
            ])
        )

    # Compute instances (VMs)
    for i, vm in enumerate(resources.get("compute_instances", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"compute_instance_{i}\" {{",
                f"  source   = \"{mod_source('compute_instance')}\"",
                f"  project_id   = var.project_id",
                f"  name         = \"{vm['name']}\"",
                f"  zone         = \"{vm.get('zone', 'us-central1-a')}\"",
                f"  machine_type = \"{vm.get('machine_type', 'e2-micro')}\"",
                f"  image        = \"{vm.get('image', 'debian-cloud/debian-11')}\"",
                f"  subnetwork   = {json.dumps(vm.get('subnetwork'))}",
                f"  create_public_ip = {str(vm.get('create_public_ip', False)).lower()}",
                f"  tags = {json.dumps(vm.get('tags', []))}",
                f"}}\n",
            ])
        )

    return "\n".join(blocks)

def run_terraform_in_dir(run_dir: str, tfvars_path: str, project_id: str) -> None:
    cwd_before = os.getcwd()
    try:
        os.chdir(run_dir)
        print(f"[INFO] Running Terraform in: {run_dir}")
        subprocess.run(["terraform", "init"], check=True)
        # Phase 1: plan for project + APIs only
        print("[INFO] Phase 1: Plan project and APIs (-target=module.project)")
        subprocess.run([
            "terraform", "plan",
            "-target=module.project",
            "-var-file", tfvars_path,
        ], check=True)
        # Phase 2: full plan for remaining resources
        print("[INFO] Phase 2: Full plan for remaining resources")
        subprocess.run([
            "terraform", "plan",
            "-var-file", tfvars_path,
        ], check=True)

        # Ask whether to apply for this project
        answer = input(f"Apply changes for project '{project_id}'? (yes/no): ")
        if answer.strip().lower() in ("yes", "y"):
            print("[INFO] Proceeding to apply...")
            # Phase 1 apply: project and APIs
            subprocess.run([
                "terraform", "apply",
                "-target=module.project",
                "-var-file", tfvars_path,
                "-auto-approve",
            ], check=True)
            # Phase 2 apply: remaining resources
            subprocess.run([
                "terraform", "apply",
                "-var-file", tfvars_path,
                "-auto-approve",
            ], check=True)
        else:
            print(f"[INFO] Skipped apply for project '{project_id}'.")
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

        # Always use core project module for project creation
        module_source_rel = rel(run_dir, os.path.join(project_root, "modules", "project"))
        write_minimal_root_tf(run_dir, module_source_rel)

        # Append resource modules based on YAML
        modules_hcl = build_module_blocks(run_dir, project_root, data)
        if modules_hcl.strip():
            with open(os.path.join(run_dir, "main.tf"), "a", encoding="utf-8") as f:
                f.write("\n\n# Additional resources from YAML\n")
                f.write(modules_hcl)

        # Write tfvars.json into run_dir
        tfvars_path = os.path.join(run_dir, "terraform.tfvars.json")
        write_tfvars_json(data, tfvars_path)

        # Execute terraform plan, then optionally apply for this run
        run_terraform_in_dir(run_dir, tfvars_path, project_id)

if __name__ == "__main__":
    main()
