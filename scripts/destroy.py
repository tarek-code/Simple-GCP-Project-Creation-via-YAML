import subprocess
import os
import sys

def run_terraform_destroy():
    # Change to project root directory (where main.tf is located)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    print(f"[INFO] Changed to project root: {project_root}")
    
    # Use the tfvars file in the project root
    tfvars_path = os.path.join(project_root, "terraform.tfvars.json")
    
    # Check if tfvars file exists
    if not os.path.exists(tfvars_path):
        print(f"[ERROR] terraform.tfvars.json not found at {tfvars_path}")
        print("Make sure you have run the deploy script first to create the tfvars file.")
        sys.exit(1)
    
    # Run terraform destroy
    print("[INFO] Starting Terraform destroy...")
    subprocess.run([
        "terraform", "destroy",
        "-var-file", tfvars_path,
        "-auto-approve"
    ], check=True)
    
    print("[INFO] Infrastructure destroyed successfully!")

def main():
    print("=== Terraform Destroy Script ===")
    print("This will destroy all infrastructure defined in your Terraform configuration.")
    print("Make sure you want to proceed with the destruction.")
    print()
    
    # Optional: Add confirmation prompt
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("Force mode: Proceeding without confirmation...")
    else:
        response = input("Are you sure you want to destroy the infrastructure? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Destroy cancelled.")
            sys.exit(0)
    
    try:
        run_terraform_destroy()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Terraform destroy failed with exit code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
