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
    # Change to project root directory (where main.tf is located)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    print(f"[INFO] Changed to project root: {project_root}")
    
    # Use the tfvars file in the project root
    tfvars_path = os.path.join(project_root, "terraform.tfvars.json")
    
    # Run terraform init
    subprocess.run(["terraform", "init"], check=True)

    # Run terraform apply
    subprocess.run([
        "terraform", "apply",
        "-var-file", tfvars_path,
        "-auto-approve"
    ], check=True)

def main():
    # Use default YAML file if no argument provided
    if len(sys.argv) == 1:
        # Default to example-project.yaml in configs directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        yaml_file = os.path.join(project_root, "configs", "example-project.yaml")
    elif len(sys.argv) == 2:
        yaml_file = sys.argv[1]
    else:
        print("Usage: python deploy.py [path-to-yaml]")
        print("If no path provided, uses configs/example-project.yaml by default")
        sys.exit(1)

    if not os.path.exists(yaml_file):
        print(f"Error: File {yaml_file} does not exist")
        sys.exit(1)

    tfvars_file = yaml_to_tfvars(yaml_file)
    run_terraform(tfvars_file)

if __name__ == "__main__":
    main()
