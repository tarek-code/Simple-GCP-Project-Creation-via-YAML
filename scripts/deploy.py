#for usage cd to this location and python deploy.py ../configs/example-project.yaml
import yaml
import json
import subprocess
import sys
import os

def yaml_to_tfvars(yaml_file, tfvars_file="terraform.tfvars.json"):
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    # Save as tfvars.json
    with open(tfvars_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[INFO] Converted {yaml_file} -> {tfvars_file}")
    return tfvars_file

def run_terraform(tfvars_file):
    # Run terraform init
    subprocess.run(["terraform", "init"], check=True)

    # Run terraform apply
    subprocess.run([
        "terraform", "apply",
        "-var-file", tfvars_file,
        "-auto-approve"
    ], check=True)

def main():
    if len(sys.argv) != 2:
        print("Usage: python deploy.py <path-to-yaml>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    if not os.path.exists(yaml_file):
        print(f"Error: File {yaml_file} does not exist")
        sys.exit(1)

    tfvars_file = yaml_to_tfvars(yaml_file)
    run_terraform(tfvars_file)

if __name__ == "__main__":
    main()
