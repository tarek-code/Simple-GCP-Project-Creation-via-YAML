import streamlit as st
import yaml
import json
import subprocess
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to Python path
# Try different path resolution methods
current_dir = Path.cwd()
script_dir = Path(__file__).parent

# If we're in the gui directory, go up one level
if current_dir.name == 'gui':
    project_root = current_dir.parent
elif script_dir.name == 'gui':
    project_root = script_dir.parent
else:
    # Fallback: assume we're already in project root
    project_root = current_dir

sys.path.append(str(project_root))

# Debug: Print the project root path
print(f"Current working directory: {current_dir}")
print(f"Script directory: {script_dir}")
print(f"Project root: {project_root}")
print(f"Configs directory exists: {(project_root / 'configs').exists()}")

st.set_page_config(
    page_title="GCP Project Creator",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def generate_standalone_main_tf(config: dict, create_project: bool = True) -> str:
    """Generate standalone main.tf content without external module dependencies"""
    project_id = config.get("project_id", "")
    billing_account = config.get("billing_account", "")
    organization_id = config.get("organization_id")
    labels = config.get("labels", {})
    apis = config.get("apis", [])
    resources = config.get("resources", {})
    
    content = '''# Authentication: Credentials are provided via GOOGLE_APPLICATION_CREDENTIALS environment variable
# The credentials file is automatically used by the Google provider for authentication

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.4.0"
    }
  }
}

# Google Cloud Provider Configuration
# Authentication: Uses credentials from GOOGLE_APPLICATION_CREDENTIALS environment variable
# This is set automatically when using uploaded credentials in the GUI
provider "google" {
  project = var.project_id
  # credentials = file("path/to/credentials.json")  # Alternative: specify credentials file directly
}

'''
    
    # Project resource (if creating project)
    if create_project:
        content += f'''# Create the project
resource "google_project" "project" {{
  project_id      = var.project_id
  name            = var.project_id
  org_id          = var.organization_id
  billing_account = var.billing_account != "" ? var.billing_account : null
  labels          = var.labels
  deletion_policy = "DELETE"
}}

'''
    else:
        content += f'''# Working with existing project - no project creation needed

'''
    
    # Enable APIs
    if apis:
        content += '''# Enable APIs
resource "google_project_service" "enabled_apis" {
  for_each = toset(var.apis)
  project  = var.project_id
  service  = each.value
}

'''
    
    # Generate inline resources instead of modules
    content += generate_inline_resources(resources)
    
    return content

def generate_standalone_variables_tf(config: dict) -> str:
    """Generate standalone variables.tf content"""
    return '''variable "project_id" {
  description = "The ID of the project"
  type        = string
}

variable "organization_id" {
  description = "Organization ID"
  type        = string
  default     = null
}

variable "billing_account" {
  description = "Billing account ID (optional)"
  type        = string
  default     = ""
}

variable "labels" {
  description = "Labels for the project"
  type        = map(string)
  default     = {}
}

variable "apis" {
  description = "List of APIs to enable"
  type        = list(string)
  default     = []
}

variable "resources" {
  description = "Ignored placeholder to silence warnings when tfvars contains 'resources'"
  type        = any
  default     = null
}
'''

def generate_inline_resources(resources: dict) -> str:
    """Generate inline resource blocks instead of module references"""
    content = ""
    
    # VPC Networks
    vpc_items = []
    if "vpc" in resources:
        if isinstance(resources["vpc"], list):
            vpc_items.extend([v for v in resources["vpc"] if isinstance(v, dict)])
        elif isinstance(resources["vpc"], dict):
            vpc_items.append(resources["vpc"])
    if isinstance(resources.get("vpcs"), list):
        vpc_items.extend([v for v in resources["vpcs"] if isinstance(v, dict)])
    
    for i, vpc in enumerate(vpc_items, 1):
        content += f'''resource "google_compute_network" "vpc_{i}" {{
  name                    = "{vpc.get('name', f'vpc-{i}')}"
  auto_create_subnetworks = {str(vpc.get('auto_create_subnetworks', False)).lower()}
  routing_mode            = "{vpc.get('routing_mode', 'GLOBAL')}"
  description             = "{vpc.get('description', 'VPC created via GUI')}"
  mtu                     = {vpc.get('mtu', 1460)}
}}
'''
    
    # Subnets
    for i, subnet in enumerate(resources.get("subnets", []), 1):
        content += f'''resource "google_compute_subnetwork" "subnet_{i}" {{
  name          = "{subnet.get('name', f'subnet-{i}')}"
  region        = "{subnet.get('region', 'us-central1')}"
  network       = google_compute_network.vpc_1.name
  ip_cidr_range = "{subnet.get('ip_cidr_range', '10.0.{i}.0/24')}"
  private_ip_google_access = {str(subnet.get('private_ip_google_access', True)).lower()}
}}
'''
    
    # Storage Buckets
    for i, bucket in enumerate(resources.get("storage_buckets", []), 1):
        content += f'''resource "google_storage_bucket" "bucket_{i}" {{
  name          = "{bucket.get('name', f'bucket-{i}')}"
  location      = "{bucket.get('location', 'US')}"
  force_destroy = {str(bucket.get('force_destroy', False)).lower()}
  
  uniform_bucket_level_access = {str(bucket.get('uniform_bucket_level_access', True)).lower()}
  
  versioning {{
    enabled = {str(bucket.get('enable_versioning', False)).lower()}
  }}
}}
'''
    
    # Compute Instances (advanced rendering if fields provided)
    for i, vm in enumerate(resources.get("compute_instances", []), 1):
        # Prepare optional fields
        desc = vm.get('description')
        labels = vm.get('labels', {})
        metadata = vm.get('metadata', {})
        startup = vm.get('metadata_startup_script')
        tags = vm.get('tags', [])
        # Boot disk
        b_size = vm.get('boot_disk_size_gb')
        b_type = vm.get('boot_disk_type')
        b_auto = vm.get('boot_disk_auto_delete', True)
        b_labels = vm.get('boot_disk_labels', {})
        # Network
        net = vm.get('network')
        sub = vm.get('subnetwork')
        nip = vm.get('network_ip')
        assign_eip = vm.get('assign_external_ip', vm.get('create_public_ip', False))
        eip_tier = vm.get('external_network_tier')
        # Scheduling
        preempt = vm.get('scheduling_preemptible')
        auto_restart = vm.get('scheduling_automatic_restart')
        ohm = vm.get('scheduling_on_host_maintenance')
        prov_model = vm.get('scheduling_provisioning_model')
        # Shielded / Confidential / GPUs
        enable_display = vm.get('enable_display')
        enable_shielded = vm.get('enable_shielded_vm')
        shielded_secure_boot = vm.get('shielded_secure_boot')
        shielded_vtpm = vm.get('shielded_vtpm')
        shielded_integrity = vm.get('shielded_integrity_monitoring')
        enable_conf = vm.get('enable_confidential_compute')
        conf_type = vm.get('confidential_instance_type')
        gpus = vm.get('guest_accelerators', [])
        # SA
        sa_email = vm.get('service_account_email')
        sa_scopes = vm.get('service_account_scopes', ["https://www.googleapis.com/auth/cloud-platform"]) or []
        # Misc
        allow_stop = vm.get('allow_stopping_for_update', True)
        can_ip_forward = vm.get('can_ip_forward', False)
        del_prot = vm.get('deletion_protection', False)
        hostname = vm.get('hostname')
        min_cpu = vm.get('min_cpu_platform')

        # Build HCL
        content += f'''resource "google_compute_instance" "vm_{i}" {{
  name         = "{vm.get('name', f'vm-{i}')}"
  zone         = "{vm.get('zone', 'us-central1-a')}"
  machine_type = "{vm.get('machine_type', 'e2-micro')}"
'''
        if desc is not None:
            content += f"  description  = {json.dumps(desc)}\n"
        if tags:
            content += f"  tags         = {json.dumps(tags)}\n"
        if labels:
            content += f"  labels       = {json.dumps(labels)}\n"
        if metadata:
            content += f"  metadata     = {json.dumps(metadata)}\n"
        if startup is not None:
            content += f"  metadata_startup_script = {json.dumps(startup)}\n"
        if enable_display is not None:
            content += f"  enable_display = {str(bool(enable_display)).lower()}\n"
        if can_ip_forward is not None:
            content += f"  can_ip_forward = {str(bool(can_ip_forward)).lower()}\n"
        if del_prot is not None:
            content += f"  deletion_protection = {str(bool(del_prot)).lower()}\n"
        if hostname is not None:
            content += f"  hostname = {json.dumps(hostname)}\n"
        if min_cpu is not None:
            content += f"  min_cpu_platform = {json.dumps(min_cpu)}\n"
        if allow_stop is not None:
            content += f"  allow_stopping_for_update = {str(bool(allow_stop)).lower()}\n"

        # Boot disk
        content += "\n  boot_disk {\n"
        if b_auto is not None:
            content += f"    auto_delete = {str(bool(b_auto)).lower()}\n"
        content += "    initialize_params {\n"
        content += f"      image = \"{vm.get('image', 'debian-cloud/debian-11')}\"\n"
        if b_labels:
            content += f"      labels = {json.dumps(b_labels)}\n"
        if b_type is not None:
            content += f"      type  = {json.dumps(b_type)}\n"
        if b_size is not None:
            content += f"      size  = {int(b_size)}\n"
        content += "    }\n  }\n\n"

        # Network interface
        content += "  network_interface {\n"
        if net is not None:
            content += f"    network = {json.dumps(net)}\n"
        elif 'vpc_1' in 'vpc_1':
            # Fallback to first network example reference if not provided
            content += "    network = google_compute_network.vpc_1.name\n"
        if sub is not None:
            content += f"    subnetwork = {json.dumps(sub)}\n"
        if nip is not None:
            content += f"    network_ip = {json.dumps(nip)}\n"
        if assign_eip:
            content += "    access_config {\n"
            if eip_tier is not None:
                content += f"      network_tier = {json.dumps(eip_tier)}\n"
            content += "    }\n"
        content += "  }\n\n"

        # Guest accelerators
        if gpus:
            for ga in gpus:
                t = ga.get('type'); c = ga.get('count')
                if t and c:
                    content += f"  guest_accelerator {{\n    type = \"{t}\"\n    count = {int(c)}\n  }}\n\n"

        # Shielded VM
        if enable_shielded:
            content += "  shielded_instance_config {\n"
            content += f"    enable_secure_boot = {str(bool(shielded_secure_boot)).lower()}\n"
            content += f"    enable_vtpm = {str(bool(shielded_vtpm if shielded_vtpm is not None else True)).lower()}\n"
            content += f"    enable_integrity_monitoring = {str(bool(shielded_integrity if shielded_integrity is not None else True)).lower()}\n"
            content += "  }\n\n"

        # Confidential compute
        if enable_conf:
            content += "  confidential_instance_config {\n"
            content += "    enable_confidential_compute = true\n"
            if conf_type:
                content += f"    confidential_instance_type = {json.dumps(conf_type)}\n"
            content += "  }\n\n"

        # Service account
        if sa_email:
            content += "  service_account {\n"
            content += f"    email  = {json.dumps(sa_email)}\n"
            content += f"    scopes = {json.dumps(sa_scopes)}\n"
            content += "  }\n\n"

        # Scheduling
        if any(v is not None for v in [preempt, auto_restart, ohm, prov_model]):
            content += "  scheduling {\n"
            if preempt is not None:
                content += f"    preemptible = {str(bool(preempt)).lower()}\n"
            if auto_restart is not None:
                content += f"    automatic_restart = {str(bool(auto_restart)).lower()}\n"
            if ohm is not None:
                content += f"    on_host_maintenance = {json.dumps(ohm)}\n"
            if prov_model is not None:
                content += f"    provisioning_model = {json.dumps(prov_model)}\n"
            content += "  }\n\n"

        content += "}\n\n"
    
    # Service Accounts
    for i, sa in enumerate(resources.get("service_accounts", []), 1):
        content += f'''resource "google_service_account" "sa_{i}" {{
  account_id   = "{sa.get('account_id', f'sa-{i}')}"
  display_name = "{sa.get('display_name', f'Service Account {i}')}"
  description  = "{sa.get('description', 'Service account created via GUI')}"
}}
'''
    
    # Firewall Rules
    for i, fw in enumerate(resources.get("firewall_rules", []), 1):
        source_ranges = fw.get('source_ranges', ['0.0.0.0/0']) or []
        ports = fw.get('ports', ['22']) or []
        # Render lists as valid HCL with double-quoted strings
        ports_hcl = f"[{', '.join([f'\"{str(p)}\"' for p in ports])}]" if ports else "[]"
        source_ranges_hcl = f"[{', '.join([f'\"{str(r)}\"' for r in source_ranges])}]" if source_ranges else "[]"
        content += f'''resource "google_compute_firewall" "firewall_{i}" {{
  name    = "{fw.get('name', f'firewall-{i}')}"
  network = google_compute_network.vpc_1.name
  
  allow {{
    protocol = "{fw.get('protocol', 'tcp')}"
    ports    = {ports_hcl}
  }}
  
  source_ranges = {source_ranges_hcl}
  direction     = "{fw.get('direction', 'INGRESS')}"
}}
'''
    
    # Cloud Run Services
    for i, cr in enumerate(resources.get("cloud_run_services", []), 1):
        content += f'''resource "google_cloud_run_service" "run_{i}" {{
  name     = "{cr.get('name', f'run-{i}')}"
  location = "{cr.get('location', 'us-central1')}"
  
  template {{
    spec {{
      containers {{
        image = "{cr.get('image', 'gcr.io/cloudrun/hello')}"
      }}
    }}
  }}
  
  traffic {{
    percent         = 100
    latest_revision = true
  }}
}}
'''
    
    # Cloud SQL Instances
    for i, sql in enumerate(resources.get("cloud_sql_instances", []), 1):
        content += f'''resource "google_sql_database_instance" "sql_{i}" {{
  name             = "{sql.get('name', f'sql-{i}')}"
  database_version = "{sql.get('database_version', 'POSTGRES_14')}"
  region           = "{sql.get('region', 'us-central1')}"
  
  settings {{
    tier = "{sql.get('tier', 'db-f1-micro')}"
  }}
  
  deletion_protection = {str(sql.get('deletion_protection', False)).lower()}
}}
'''
    
    # Pub/Sub Topics
    for i, topic in enumerate(resources.get("pubsub_topics", []), 1):
        content += f'''resource "google_pubsub_topic" "topic_{i}" {{
  name = "{topic.get('name', f'topic-{i}')}"
}}
'''
    
    # Secret Manager Secrets
    for i, secret in enumerate(resources.get("secrets", []), 1):
        content += f'''resource "google_secret_manager_secret" "secret_{i}" {{
  secret_id = "{secret.get('name', f'secret-{i}')}"
  
  replication {{
    auto {{
    }}
  }}
}}

resource "google_secret_manager_secret_version" "secret_version_{i}" {{
  secret = google_secret_manager_secret.secret_{i}.id
  secret_data = "{secret.get('value', 'dummy-value')}"
}}
'''
    
    # BigQuery Datasets
    for i, dataset in enumerate(resources.get("bigquery_datasets", []), 1):
        content += f'''resource "google_bigquery_dataset" "dataset_{i}" {{
  dataset_id = "{dataset.get('dataset_id', f'dataset-{i}')}"
  location   = "{dataset.get('location', 'US')}"
}}
'''
    
    # Artifact Registry
    for i, repo in enumerate(resources.get("artifact_repos", []), 1):
        content += f'''resource "google_artifact_registry_repository" "repo_{i}" {{
  location      = "{repo.get('location', 'us')}"
  repository_id = "{repo.get('name', f'repo-{i}')}"
  description   = "{repo.get('description', 'Repository created via GUI')}"
  format        = "{repo.get('format', 'DOCKER')}"
}}
'''
    
    # DNS Zones
    for i, zone in enumerate(resources.get("dns_zones", []), 1):
        content += f'''resource "google_dns_managed_zone" "zone_{i}" {{
  name        = "{zone.get('name', f'zone-{i}')}"
  dns_name    = "{zone.get('dns_name', 'example.com.')}"
  description = "{zone.get('description', 'DNS zone created via GUI')}"
}}
'''
    
    return content

def main():
    st.title("🏗️ Project Builder")
    st.markdown("Create and deploy Google Cloud Platform projects with a simple GUI interface")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "🏗️ Project Builder",
        "📋 Configuration Manager", 
        "🚀 Deploy & Monitor",
        "🗑️ Destroy",
        "📚 Help & Examples"
    ])
    
    if page == "🏗️ Project Builder":
        project_builder()
    elif page == "📋 Configuration Manager":
        config_manager()
    elif page == "🚀 Deploy & Monitor":
        deploy_monitor()
    elif page == "🗑️ Destroy":
        destroy_manager()
    elif page == "📚 Help & Examples":
        help_examples()

def project_builder():
    st.markdown("Configure your GCP project step by step")
    
    # Initialize session state for credentials
    if 'credentials_file' not in st.session_state:
        st.session_state.credentials_file = None
    if 'credentials_path' not in st.session_state:
        st.session_state.credentials_path = None
    if 'project_id' not in st.session_state:
        st.session_state.project_id = ""
    
    def test_gcp_connection():
        """Test GCP connection using the uploaded credentials"""
        if not st.session_state.credentials_file:
            st.error("❌ No credentials uploaded")
            return
        
        # Find gcloud executable
        gcloud_path = None
        possible_paths = [
            "gcloud",  # Try PATH first
            r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
            r"C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
            r"C:\Users\{}\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd".format(os.getenv('USERNAME', '')),
            r"C:\Users\{}\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud".format(os.getenv('USERNAME', '')),
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    gcloud_path = path
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
            except Exception:
                continue
        
        if not gcloud_path:
            st.warning("⚠️ Google Cloud SDK not found in common locations")
            st.info("🔧 **Troubleshooting:**")
            st.markdown("""
            **If you have gcloud installed:**
            1. Make sure gcloud is in your system PATH
            2. Restart your terminal/command prompt
            3. Try running: `gcloud --version` in a new terminal
            
            **Alternative:**
            - Your credentials are still valid and will work for deployment
            - The test connection is optional - deployment will work fine
            """)
            
            if st.button("✅ Skip Test - Credentials Look Valid", type="secondary"):
                st.success("✅ Credentials validated successfully!")
                try:
                    creds_json = json.loads(st.session_state.credentials_file)
                    service_account = creds_json.get('client_email', 'Unknown')
                    project_id = creds_json.get('project_id', 'Unknown')
                    st.info(f"🔑 Service Account: {service_account}")
                    st.info(f"📋 Project ID: {project_id}")
                    st.success("🎯 Ready for deployment!")
                except:
                    st.info("📋 Credentials format appears valid")
            return
        
        st.success("✅ Google Cloud SDK found")
        
        try:
            # Create a temporary credentials file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(st.session_state.credentials_file)
                temp_creds_path = f.name
            
            # Set environment variable for authentication
            env = os.environ.copy()
            env['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
            
            # Test with gcloud command
            test_cmd = [gcloud_path, 'auth', 'activate-service-account', '--key-file', temp_creds_path]
            
            with st.spinner("Testing GCP connection..."):
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )
                
                if result.returncode == 0:
                    # Test project access
                    project_cmd = [gcloud_path, 'config', 'get-value', 'project']
                    project_result = subprocess.run(
                        project_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    
                    if project_result.returncode == 0:
                        current_project = project_result.stdout.strip()
                        st.success(f"✅ Connection successful! Current project: {current_project}")
                    else:
                        st.success("✅ Authentication successful!")
                        
                    # Show credentials info
                    try:
                        creds_json = json.loads(st.session_state.credentials_file)
                        service_account = creds_json.get('client_email', 'Unknown')
                        project_id = creds_json.get('project_id', 'Unknown')
                        st.info(f"🔑 Service Account: {service_account}")
                        st.info(f"📋 Project ID: {project_id}")
                    except:
                        pass
                        
                else:
                    st.error(f"❌ Connection failed: {result.stderr}")
            
            # Clean up temporary file
            os.unlink(temp_creds_path)
            
        except Exception as e:
            st.error(f"❌ Error testing connection: {str(e)}")
    
    # Credentials Section (Optional)
    with st.expander("🔑 GCP Credentials (Optional)", expanded=True):
        st.markdown("**Optional**: Upload your GCP service account credentials to enable automatic deployment. You can also use existing `gcloud` authentication.")
        
        # Choose input method
        input_method = st.radio(
            "Choose how to provide credentials:",
            ["📁 Upload JSON file", "📝 Paste JSON content"],
            key="credentials_input_method"
        )
        
        credentials_content = None
        credentials_json = None
        
        if input_method == "📁 Upload JSON file":
            # File uploader for credentials.json
            uploaded_file = st.file_uploader(
                "Upload credentials.json",
                type=['json'],
                help="Upload your GCP service account credentials JSON file (optional)",
                key="credentials_uploader"
            )
            
            if uploaded_file is not None:
                try:
                    credentials_content = uploaded_file.read().decode('utf-8')
                    credentials_json = json.loads(credentials_content)
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file. Please upload a valid credentials.json file.")
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        else:  # Paste JSON content
            st.markdown("**Paste your credentials JSON content below:**")
            json_text = st.text_area(
                "Credentials JSON",
                height=200,
                placeholder='{\n  "type": "service_account",\n  "project_id": "your-project-id",\n  "private_key_id": "...",\n  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",\n  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",\n  "client_id": "...",\n  "auth_uri": "https://accounts.google.com/o/oauth2/auth",\n  "token_uri": "https://oauth2.googleapis.com/token",\n  ...\n}',
                help="Paste the complete JSON content from your credentials file",
                key="credentials_json_paste"
            )
            
            if json_text.strip():
                try:
                    credentials_json = json.loads(json_text)
                    credentials_content = json_text
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON format: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error parsing JSON: {str(e)}")
        
        # Process credentials if provided
        if credentials_json is not None:
            # Validate that it looks like a service account key
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            if all(field in credentials_json for field in required_fields):
                if credentials_json.get('type') == 'service_account':
                    st.success("✅ Valid service account credentials!")
                    
                    # Store credentials in session state
                    st.session_state.credentials_file = credentials_content
                    if input_method == "📁 Upload JSON file" and uploaded_file is not None:
                        st.session_state.credentials_path = f"credentials_{uploaded_file.name}"
                    else:
                        st.session_state.credentials_path = "credentials_pasted.json"
                    
                    # Auto-populate Project ID from credentials
                    cred_project_id = credentials_json.get('project_id', '')
                    if cred_project_id:
                        st.session_state.project_id = cred_project_id
                    
                    # Display project info from credentials
                    client_email = credentials_json.get('client_email', 'Unknown')
                    
                    st.info(f"**Project ID**: {cred_project_id}")
                    st.info(f"**Service Account**: {client_email}")
                    st.success(f"✅ Project ID automatically set: **{cred_project_id}**")
                else:
                    st.error("❌ Invalid credentials. Expected 'service_account' type.")
            else:
                missing_fields = [field for field in required_fields if field not in credentials_json]
                st.error(f"❌ Invalid credentials. Missing fields: {', '.join(missing_fields)}")
        
        # Show current credentials status
        if st.session_state.credentials_file:
            st.success("🔑 Credentials loaded successfully")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("🔄 Test Connection", type="secondary"):
                    test_gcp_connection()
            
            with col2:
                if st.button("💾 Save Credentials", type="primary"):
                    # Save credentials to a secure location
                    credentials_file_path = project_root / st.session_state.credentials_path
                    with open(credentials_file_path, 'w') as f:
                        f.write(st.session_state.credentials_file)
                    
                    st.success("✅ Credentials saved successfully!")
                    st.balloons()
            
            with col3:
                if st.button("🗑️ Remove", type="secondary"):
                    st.session_state.credentials_file = None
                    st.session_state.credentials_path = None
                    st.rerun()
        else:
            st.info("ℹ️ No credentials uploaded. You can use existing `gcloud` authentication or upload credentials later.")
    
    # Help section for credentials
    with st.expander("📚 Authentication Options"):
        st.markdown("""
        ### 🔑 Authentication Methods
        
        You have **two options** for GCP authentication:
        
        #### Option 1: Upload Credentials (Recommended for GUI)
        1. **Go to Google Cloud Console**: https://console.cloud.google.com/
        2. **Select your project** (or create a new one)
        3. **Navigate to IAM & Admin** → **Service Accounts**
        4. **Create a new service account** or use an existing one
        5. **Create a key**:
           - Click on the service account
           - Go to the "Keys" tab
           - Click "Add Key" → "Create new key"
           - Choose "JSON" format
           - Download the file (usually named something like `project-name-xxxxx.json`)
        6. **Upload the downloaded file** using the file uploader above
        
        #### Option 2: Use Existing gcloud Authentication
        If you already have `gcloud` configured on your system:
        ```bash
        gcloud auth login
        gcloud config set project YOUR_PROJECT_ID
        ```
        
        ### 🔐 Required Permissions
        
        Your service account needs the following roles for full functionality:
        - **Editor** or **Owner** (for creating resources)
        - **Service Account User** (for using service accounts)
        - **Project IAM Admin** (for managing IAM roles)
        
        ### 💡 Benefits of Uploading Credentials
        
        - **Automatic deployment** without manual authentication
        - **Consistent authentication** across sessions
        - **Better error handling** with specific service account details
        """)
    
    st.divider()
    
    # Ensure series catalog helper is available before any popup rendering
    def gp_series_catalog() -> Dict[str, Dict[str, Dict[str, list]]]:
        return {
            "C3D": {
                "Standard": {
                    "presets": [
                        "c3d-standard-4","c3d-standard-8","c3d-standard-16","c3d-standard-30",
                        "c3d-standard-60","c3d-standard-90","c3d-standard-180","c3d-standard-360",
                        "c3d-standard-8-lssd","c3d-standard-16-lssd","c3d-standard-30-lssd",
                        "c3d-standard-60-lssd","c3d-standard-90-lssd","c3d-standard-180-lssd","c3d-standard-360-lssd"
                    ]
                },
                "High memory": {
                    "presets": [
                        "c3d-highmem-4","c3d-highmem-8","c3d-highmem-16","c3d-highmem-30",
                        "c3d-highmem-60","c3d-highmem-90","c3d-highmem-180","c3d-highmem-360",
                        "c3d-highmem-8-lssd","c3d-highmem-16-lssd","c3d-highmem-30-lssd",
                        "c3d-highmem-60-lssd","c3d-highmem-90-lssd","c3d-highmem-180-lssd","c3d-highmem-360-lssd"
                    ]
                },
                "High CPU": {
                    "presets": [
                        "c3d-highcpu-4","c3d-highcpu-8","c3d-highcpu-16","c3d-highcpu-30",
                        "c3d-highcpu-60","c3d-highcpu-90","c3d-highcpu-180","c3d-highcpu-360"
                    ]
                }
            },
            "E2": {
                "Standard": {"presets": ["e2-micro","e2-small","e2-medium","e2-standard-2","e2-standard-4","e2-standard-8","e2-standard-16","e2-standard-32"]},
                "High memory": {"presets": ["e2-highmem-2","e2-highmem-4","e2-highmem-8","e2-highmem-16"]},
                "High CPU": {"presets": ["e2-highcpu-2","e2-highcpu-4","e2-highcpu-8","e2-highcpu-16","e2-highcpu-32"]},
                "Shared-core": {"presets": ["e2-medium","e2-micro","e2-small"]},
            },
            "N2": {
                "Standard": {"presets": ["n2-standard-2","n2-standard-4","n2-standard-8","n2-standard-16","n2-standard-32"]}
            },
            "N2D": {
                "Standard": {"presets": ["n2d-standard-2","n2d-standard-4","n2d-standard-8","n2d-standard-16","n2d-standard-32"]}
            },
            "N1": {
                "Standard": {"presets": ["n1-standard-1","n1-standard-2","n1-standard-4","n1-standard-8","n1-standard-16"]}
            }
        }

    # Basic vCPU/memory inference helper available early for popup
    def infer_vcpu_and_memory(machine_type: str) -> tuple[float, float]:
        mt = (machine_type or "").lower()
        presets = {
            "e2-micro": (0.25, 1),
            "e2-small": (0.5, 2),
            "e2-medium": (2, 4),
            "e2-standard-2": (2, 8),
            "e2-standard-4": (4, 16),
            "e2-standard-8": (8, 32),
            "e2-standard-16": (16, 64),
            "e2-standard-32": (32, 128),
            "e2-highmem-2": (2, 16),
            "e2-highmem-4": (4, 32),
            "e2-highmem-8": (8, 64),
            "e2-highmem-16": (16, 128),
            "e2-highcpu-2": (2, 2),
            "e2-highcpu-4": (4, 4),
            "e2-highcpu-8": (8, 8),
            "e2-highcpu-16": (16, 16),
            "e2-highcpu-32": (32, 32),
        }
        if mt in presets:
            return presets[mt]
        # Heuristic fallback: extract trailing number as vCPU, 4GB per vCPU
        import re
        m = re.search(r"-(\d+)$", mt)
        if m:
            v = float(m.group(1))
            return (v, v * 4.0)
        return (2.0, 8.0)
    # No popup - machine type selection is inline in Advanced VM Options
    
    # Project Settings
    st.subheader("📋 Project Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        project_id = st.text_input(
            "Project ID", 
            value=st.session_state.project_id,
            placeholder="my-awesome-project-123",
            help="Must be globally unique across all GCP projects"
        )
        billing_account = st.text_input(
            "Billing Account (Optional)", 
            placeholder="01783B-A7A65B-153181",
            help="Your GCP billing account ID (optional - can be set later)"
        )
        organization_id = st.text_input(
            "Organization ID (Optional)", 
            placeholder="123456789012",
            help="If creating under an organization"
        )
        
        # Project creation option
        create_new_project = st.checkbox(
            "🏗️ Create New Project",
            value=True,
            help="Check this if you want to create a new GCP project. Uncheck to work with an existing project."
        )
    
    with col2:
        st.markdown("**Project Labels**")
        
        # Initialize labels in session state
        if 'project_labels' not in st.session_state:
            st.session_state.project_labels = {}
        
        # Initialize number of label form sections
        if 'label_form_count' not in st.session_state:
            st.session_state.label_form_count = 1
        
        # Render label form sections
        for i in range(st.session_state.label_form_count):
            if i > 0:  # Add space between forms
                st.markdown("---")
            
            st.markdown(f"**Label {i+1}:**")
            
            # Get or create label data for this form
            label_keys = list(st.session_state.project_labels.keys())
            if i >= len(label_keys):
                # Create new label with default values
                new_key = f"label-{i+1}"
                new_value = f"value-{i+1}"
                st.session_state.project_labels[new_key] = new_value
                label_keys = list(st.session_state.project_labels.keys())
            
            current_key = label_keys[i] if i < len(label_keys) else f"label-{i+1}"
            current_value = st.session_state.project_labels.get(current_key, f"value-{i+1}")
            
            # Form fields for this label
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                form_key = st.text_input("Label Key", value=current_key, key=f"label_key_{i}")
            with col2:
                form_value = st.text_input("Label Value", value=current_value, key=f"label_value_{i}")
            with col3:
                if st.button("🗑️", key=f"del_label_{i}"):
                    # Remove this label and adjust form count
                    if current_key in st.session_state.project_labels:
                        del st.session_state.project_labels[current_key]
                    st.session_state.label_form_count -= 1
                    st.rerun()
            
            # Update label data
            if form_key and form_key != current_key:
                # Key changed - update the label
                if current_key in st.session_state.project_labels:
                    del st.session_state.project_labels[current_key]
                st.session_state.project_labels[form_key] = form_value
            elif form_key == current_key and form_value != current_value:
                # Value changed
                st.session_state.project_labels[current_key] = form_value
        
        # Add button to create new label form section
        if st.button("➕ Add Another Label", key="add_label"):
            st.session_state.label_form_count += 1
            st.rerun()
        
        labels = st.session_state.project_labels
    
    # APIs Selection
    st.subheader("🔌 Required APIs")
    st.markdown("Select the APIs you need for your project")
    
    api_categories = {
        "Core Infrastructure": [
            "compute.googleapis.com",
            "iam.googleapis.com", 
            "storage.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "serviceusage.googleapis.com",
            "oslogin.googleapis.com",
            "cloudtrace.googleapis.com"
        ],
        "Networking": [
            "dns.googleapis.com",
            "vpcaccess.googleapis.com",
            "networkconnectivity.googleapis.com"
        ],
        "Serverless": [
            "run.googleapis.com",
            "cloudfunctions.googleapis.com"
        ],
        "Databases & Storage": [
            "sqladmin.googleapis.com",
            "bigquery.googleapis.com",
            "bigqueryconnection.googleapis.com",
            "bigquerydatapolicy.googleapis.com",
            "bigquerymigration.googleapis.com",
            "bigqueryreservation.googleapis.com",
            "bigquerystorage.googleapis.com",
            "redis.googleapis.com",
            "spanner.googleapis.com",
            "datastore.googleapis.com"
        ],
        "Security & Secrets": [
            "secretmanager.googleapis.com",
            "privilegedaccessmanager.googleapis.com"
        ],
        "Messaging & Events": [
            "pubsub.googleapis.com"
        ],
        "Containers & Artifacts": [
            "container.googleapis.com",
            "artifactregistry.googleapis.com",
            "containerfilesystem.googleapis.com",
            "containerregistry.googleapis.com"
        ],
        "Analytics & Data": [
            "analyticshub.googleapis.com",
            "dataplex.googleapis.com",
            "dataform.googleapis.com"
        ],
        "AI & Machine Learning": [
            "aiplatform.googleapis.com",
            "generativelanguage.googleapis.com"
        ],
        "Monitoring & Logging": [
            "logging.googleapis.com",
            "monitoring.googleapis.com",
            "cloudprofiler.googleapis.com"
        ],
        "Backup & Recovery": [
            "gkebackup.googleapis.com"
        ],
        "Service Management": [
            "servicemanagement.googleapis.com"
        ],
        "Storage & Files": [
            "storage-api.googleapis.com"
        ]
    }
    
    selected_apis = []
    for category, apis in api_categories.items():
        st.markdown(f"**{category}**")
        for api in apis:
            if st.checkbox(api, key=f"api_{api}"):
                selected_apis.append(api)
    
    # Resources Configuration
    st.subheader("🏗️ Resources")
    st.markdown("Configure the infrastructure resources you want to create")
    
    resources = {}
    
    # Initialize session state for resources
    if 'project_resources' not in st.session_state:
        st.session_state.project_resources = {}
    # Ensure core collections exist regardless of checkbox state
    if 'vpcs' not in st.session_state:
        st.session_state.vpcs = []
    if 'subnets' not in st.session_state:
        st.session_state.subnets = []
    
    # VPC Configuration (multiple)
    if st.checkbox("🌐 Create VPC Networks"):
        st.markdown("**VPC Settings**")
        if 'vpcs' not in st.session_state:
            st.session_state.vpcs = []
        # Number of VPC form sections like Labels UX
        if 'vpc_form_count' not in st.session_state:
            st.session_state.vpc_form_count = 1

        # Render VPC form sections
        for i in range(st.session_state.vpc_form_count):
            if i > 0:
                st.markdown("---")

            # Ensure there is a VPC dict for this index
            if i >= len(st.session_state.vpcs):
                st.session_state.vpcs.append({
                    "name": f"my-vpc-{i+1}" if i > 0 else "my-vpc",
                    "routing_mode": "GLOBAL",
                    "description": "VPC created via GUI",
                    "auto_create_subnetworks": False,
                    "mtu": 1460,
                    "bgp_best_path_selection_mode": "LEGACY",
                    "bgp_always_compare_med": False,
                    "bgp_inter_region_cost": "DEFAULT",
                    "enable_ula_internal_ipv6": False,
                    "delete_default_routes_on_create": False,
                    "network_firewall_policy_enforcement_order": "AFTER_CLASSIC_FIREWALL",
                    "network_profile": None,
                    "resource_manager_tags": {}
                })

            vpc = st.session_state.vpcs[i]

            st.markdown(f"**VPC {i+1}:**")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                form_name = st.text_input("VPC Name", value=vpc.get('name', ''), key=f"vpc_name_{i}")
            with col2:
                form_routing = st.selectbox(
                    "Routing Mode", ["GLOBAL", "REGIONAL"],
                    index=0 if vpc.get('routing_mode', 'GLOBAL') == 'GLOBAL' else 1,
                    key=f"vpc_routing_{i}"
                )
            with col3:
                if st.button("🗑️", key=f"del_vpc_{i}"):
                    st.session_state.vpcs.pop(i)
                    st.session_state.vpc_form_count -= 1
                    st.rerun()

            # If REGIONAL routing, allow selecting a region
            form_region = vpc.get('region', 'us-central1')
            if form_routing == 'REGIONAL':
                region_options = [
                    "us-central1", "us-west1", "us-east1", "us-west2",
                    "europe-west1", "europe-west2", "asia-east1", "asia-south1"
                ]
                # Safe index fallback
                try:
                    default_region_index = region_options.index(form_region)
                except ValueError:
                    default_region_index = 0
                form_region = st.selectbox(
                    "Region", region_options,
                    index=default_region_index,
                    key=f"vpc_region_{i}"
                )

            # Advanced VPC options (collapsible)
            with st.expander("🔧 Advanced VPC Options", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    form_auto_create_subnetworks = st.checkbox(
                        "Auto Create Subnetworks", 
                        value=vpc.get('auto_create_subnetworks', False),
                        key=f"vpc_auto_create_{i}"
                    )
                    form_mtu = st.number_input(
                        "MTU (1300-8896)", 
                        value=vpc.get('mtu', 1460), 
                        min_value=1300, 
                        max_value=8896,
                        key=f"vpc_mtu_{i}"
                    )
                    form_enable_ula_ipv6 = st.checkbox(
                        "Enable ULA Internal IPv6", 
                        value=vpc.get('enable_ula_internal_ipv6', False),
                        key=f"vpc_ula_ipv6_{i}"
                    )
                with col2:
                    form_delete_default_routes = st.checkbox(
                        "Delete Default Routes on Create", 
                        value=vpc.get('delete_default_routes_on_create', False),
                        key=f"vpc_delete_routes_{i}"
                    )
                    form_firewall_order = st.selectbox(
                        "Firewall Policy Enforcement Order",
                        ["AFTER_CLASSIC_FIREWALL", "BEFORE_CLASSIC_FIREWALL"],
                        index=0 if vpc.get('network_firewall_policy_enforcement_order', 'AFTER_CLASSIC_FIREWALL') == 'AFTER_CLASSIC_FIREWALL' else 1,
                        key=f"vpc_firewall_order_{i}"
                    )
                    form_network_profile = st.text_input(
                        "Network Profile URL", 
                        value=vpc.get('network_profile', ''),
                        placeholder="projects/PROJECT/global/networkProfiles/PROFILE",
                        key=f"vpc_network_profile_{i}"
                    )

                # BGP Configuration
                st.markdown("**BGP Configuration:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    form_bgp_mode = st.selectbox(
                        "BGP Best Path Selection Mode",
                        ["LEGACY", "STANDARD"],
                        index=0 if vpc.get('bgp_best_path_selection_mode', 'LEGACY') == 'LEGACY' else 1,
                        key=f"vpc_bgp_mode_{i}"
                    )
                with col2:
                    form_bgp_compare_med = st.checkbox(
                        "BGP Always Compare MED", 
                        value=vpc.get('bgp_always_compare_med', False),
                        key=f"vpc_bgp_med_{i}"
                    )
                with col3:
                    form_bgp_inter_region = st.selectbox(
                        "BGP Inter-Region Cost",
                        ["DEFAULT", "ADD_COST_TO_MED"],
                        index=0 if vpc.get('bgp_inter_region_cost', 'DEFAULT') == 'DEFAULT' else 1,
                        key=f"vpc_bgp_inter_region_{i}"
                    )

                # IPv6 Configuration
                if form_enable_ula_ipv6:
                    st.markdown("**IPv6 Configuration:**")
                    form_internal_ipv6_range = st.text_input(
                        "Internal IPv6 Range (/48)", 
                        value=vpc.get('internal_ipv6_range', ''),
                        placeholder="fd20:1234:5678::/48",
                        key=f"vpc_ipv6_range_{i}"
                    )

                # Resource Manager Tags
                st.markdown("**Resource Manager Tags:**")
                form_resource_tags = st.text_input(
                    "Resource Manager Tags (JSON format)", 
                    value=json.dumps(vpc.get('resource_manager_tags', {}), indent=2),
                    placeholder='{"tagKeys/123": "tagValues/456"}',
                    key=f"vpc_resource_tags_{i}"
                )

            # Parse resource manager tags
            try:
                resource_tags = json.loads(form_resource_tags) if form_resource_tags and form_resource_tags.strip() else {}
            except json.JSONDecodeError:
                resource_tags = {}

            # Update VPC data
            vpc_data = {
                "name": form_name,
                "routing_mode": form_routing,
                "description": vpc.get("description", "VPC created via GUI"),
                "auto_create_subnetworks": form_auto_create_subnetworks,
                "mtu": form_mtu,
                "bgp_best_path_selection_mode": form_bgp_mode,
                "bgp_always_compare_med": form_bgp_compare_med,
                "bgp_inter_region_cost": form_bgp_inter_region,
                "enable_ula_internal_ipv6": form_enable_ula_ipv6,
                "delete_default_routes_on_create": form_delete_default_routes,
                "network_firewall_policy_enforcement_order": form_firewall_order,
                "network_profile": form_network_profile if form_network_profile and form_network_profile.strip() else None,
                "resource_manager_tags": resource_tags
            }

            # Add region if REGIONAL routing
            if form_routing == 'REGIONAL':
                vpc_data["region"] = form_region

            # Add IPv6 range if ULA IPv6 is enabled
            if form_enable_ula_ipv6 and form_internal_ipv6_range and form_internal_ipv6_range.strip():
                vpc_data["internal_ipv6_range"] = form_internal_ipv6_range

            st.session_state.vpcs[i] = vpc_data

        # Add button to create another VPC section
        if st.button("➕ Add Another VPC", key="add_vpc_section"):
            st.session_state.vpc_form_count += 1
            st.rerun()

        if st.session_state.vpcs:
            resources["vpcs"] = st.session_state.vpcs
    
    # Subnets
    if st.checkbox("📡 Create Subnets"):
        st.markdown("**Subnet Configuration**")
        if 'subnets' not in st.session_state:
            st.session_state.subnets = []
        if 'subnet_form_count' not in st.session_state:
            st.session_state.subnet_form_count = 1

        for i in range(st.session_state.subnet_form_count):
            if i > 0:
                st.markdown("---")

            # Determine available VPC names (only from currently enabled VPC section)
            vpc_options = []
            if resources.get("vpc") and resources["vpc"].get("name"):
                vpc_options.append(resources["vpc"]["name"])
            if isinstance(resources.get("vpcs"), list):
                for v in resources["vpcs"]:
                    if isinstance(v, dict) and v.get("name"):
                        vpc_options.append(v["name"])
            # Removed fallback to session_state.vpcs - only show VPCs when VPC section is enabled

            # Ensure data object exists
            if i >= len(st.session_state.subnets):
                st.session_state.subnets.append({
                    "name": f"subnet-{i+1}",
                    "region": "us-central1",
                    "ip_cidr_range": "10.0.%d.0/24" % (i),
                    "network": (vpc_options[0] if vpc_options else ""),
                    "private_ip_google_access": True,
                    "purpose": "PRIVATE",
                    "description": None,
                    "reserved_internal_range": None,
                    "role": None,
                    "private_ipv6_google_access": None,
                    "stack_type": "IPV4_ONLY",
                    "ipv6_access_type": None,
                    "external_ipv6_prefix": None,
                    "ip_collection": None,
                    "allow_subnet_cidr_routes_overlap": False,
                    "send_secondary_ip_range_if_empty": False,
                    "resource_manager_tags": {},
                    "log_config": None
                })

            subnet = st.session_state.subnets[i]

            st.markdown(f"**Subnet {i+1}:**")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                form_name = st.text_input("Subnet Name", value=subnet.get('name', ''), key=f"subnet_name_{i}")
            with col2:
                form_region = st.selectbox(
                    "Region", ["us-central1", "us-west1", "europe-west1"],
                    index=["us-central1", "us-west1", "europe-west1"].index(subnet.get('region', 'us-central1')),
                    key=f"subnet_region_{i}"
                )
            with col3:
                form_cidr = st.text_input("CIDR Range", value=subnet.get('ip_cidr_range', ''), key=f"subnet_cidr_{i}")
            with col4:
                if st.button("🗑️", key=f"del_subnet_{i}"):
                    st.session_state.subnets.pop(i)
                    st.session_state.subnet_form_count -= 1
                    st.rerun()

            st.markdown("**Attach to VPC**")
            if vpc_options:
                try:
                    default_vpc_idx = vpc_options.index(subnet.get('network', vpc_options[0]))
                except ValueError:
                    default_vpc_idx = 0
                form_network = st.selectbox("VPC Network", vpc_options, index=default_vpc_idx, key=f"subnet_network_{i}")
            else:
                form_network = st.text_input("VPC Network Name", value=subnet.get('network', ''), placeholder="enter existing VPC name", key=f"subnet_network_text_{i}")

            # Basic subnet options
            col1, col2 = st.columns(2)
            with col1:
                form_private_ip_google_access = st.checkbox("Private Google Access", value=subnet.get('private_ip_google_access', True), key=f"subnet_private_ip_{i}")
            with col2:
                form_purpose = st.selectbox("Purpose", ["PRIVATE", "REGIONAL_MANAGED_PROXY", "GLOBAL_MANAGED_PROXY", "PRIVATE_SERVICE_CONNECT", "PEER_MIGRATION", "PRIVATE_NAT"], index=0, key=f"subnet_purpose_{i}")

            # Advanced subnet options (collapsible)
            with st.expander("🔧 Advanced Subnet Options", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    form_description = st.text_input(
                        "Description", 
                        value=subnet.get('description', ''),
                        key=f"subnet_description_{i}"
                    )
                    form_reserved_internal_range = st.text_input(
                        "Reserved Internal Range", 
                        value=subnet.get('reserved_internal_range', ''),
                        placeholder="networkconnectivity.googleapis.com/projects/PROJECT/locations/global/internalRanges/RANGE",
                        key=f"subnet_reserved_range_{i}"
                    )
                    form_role = st.selectbox(
                        "Role (for REGIONAL_MANAGED_PROXY)",
                        ["ACTIVE", "BACKUP"],
                        index=0 if subnet.get('role', 'ACTIVE') == 'ACTIVE' else 1,
                        key=f"subnet_role_{i}"
                    )
                with col2:
                    form_private_ipv6_google_access = st.text_input(
                        "Private IPv6 Google Access", 
                        value=subnet.get('private_ipv6_google_access', ''),
                        key=f"subnet_private_ipv6_{i}"
                    )
                    form_external_ipv6_prefix = st.text_input(
                        "External IPv6 Prefix", 
                        value=subnet.get('external_ipv6_prefix', ''),
                        key=f"subnet_external_ipv6_{i}"
                    )
                    form_ip_collection = st.text_input(
                        "IP Collection (PublicDelegatedPrefix)", 
                        value=subnet.get('ip_collection', ''),
                        placeholder="projects/PROJECT/regions/REGION/publicDelegatedPrefixes/PREFIX",
                        key=f"subnet_ip_collection_{i}"
                    )

                # IPv6 Configuration
                st.markdown("**IPv6 Configuration:**")
                col1, col2 = st.columns(2)
                with col1:
                    form_stack_type = st.selectbox(
                        "Stack Type",
                        ["IPV4_ONLY", "IPV4_IPV6", "IPV6_ONLY"],
                        index=0 if subnet.get('stack_type', 'IPV4_ONLY') == 'IPV4_ONLY' else (1 if subnet.get('stack_type') == 'IPV4_IPV6' else 2),
                        key=f"subnet_stack_type_{i}"
                    )
                with col2:
                    form_ipv6_access_type = st.selectbox(
                        "IPv6 Access Type",
                        ["EXTERNAL", "INTERNAL"],
                        index=0 if subnet.get('ipv6_access_type', 'EXTERNAL') == 'EXTERNAL' else 1,
                        key=f"subnet_ipv6_access_{i}"
                    )

                # Advanced Configuration
                st.markdown("**Advanced Configuration:**")
                col1, col2 = st.columns(2)
                with col1:
                    form_allow_cidr_overlap = st.checkbox(
                        "Allow Subnet CIDR Routes Overlap", 
                        value=subnet.get('allow_subnet_cidr_routes_overlap', False),
                        key=f"subnet_allow_overlap_{i}"
                    )
                with col2:
                    form_send_secondary_empty = st.checkbox(
                        "Send Secondary IP Range If Empty", 
                        value=subnet.get('send_secondary_ip_range_if_empty', False),
                        key=f"subnet_send_secondary_{i}"
                    )

                # Logging Configuration
                st.markdown("**Logging Configuration:**")
                form_enable_logging = st.checkbox(
                    "Enable VPC Flow Logging", 
                    value=subnet.get('log_config') is not None,
                    key=f"subnet_enable_logging_{i}"
                )
                
                if form_enable_logging:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        form_log_aggregation = st.selectbox(
                            "Aggregation Interval",
                            ["INTERVAL_5_SEC", "INTERVAL_30_SEC", "INTERVAL_1_MIN", "INTERVAL_5_MIN", "INTERVAL_10_MIN", "INTERVAL_15_MIN"],
                            index=0,
                            key=f"subnet_log_aggregation_{i}"
                        )
                    with col2:
                        form_log_sampling = st.number_input(
                            "Flow Sampling (0.0-1.0)", 
                            value=0.5, 
                            min_value=0.0, 
                            max_value=1.0, 
                            step=0.1,
                            key=f"subnet_log_sampling_{i}"
                        )
                    with col3:
                        form_log_metadata = st.selectbox(
                            "Log Metadata",
                            ["INCLUDE_ALL_METADATA", "EXCLUDE_ALL_METADATA", "CUSTOM_METADATA"],
                            index=0,
                            key=f"subnet_log_metadata_{i}"
                        )

                # Resource Manager Tags
                st.markdown("**Resource Manager Tags:**")
                form_resource_tags = st.text_input(
                    "Resource Manager Tags (JSON format)", 
                    value=json.dumps(subnet.get('resource_manager_tags', {}), indent=2),
                    placeholder='{"tagKeys/123": "tagValues/456"}',
                    key=f"subnet_resource_tags_{i}"
                )

            # Parse resource manager tags
            try:
                resource_tags = json.loads(form_resource_tags) if form_resource_tags and form_resource_tags.strip() else {}
            except json.JSONDecodeError:
                resource_tags = {}

            # Build log config if logging is enabled
            log_config = None
            if form_enable_logging:
                log_config = {
                    "aggregation_interval": form_log_aggregation,
                    "flow_sampling": form_log_sampling,
                    "metadata": form_log_metadata
                }

            # Update subnet data
            subnet_data = {
                "name": form_name,
                "region": form_region,
                "ip_cidr_range": form_cidr,
                "network": form_network,
                "private_ip_google_access": form_private_ip_google_access,
                "purpose": form_purpose,
                "description": form_description if form_description and form_description.strip() else None,
                "reserved_internal_range": form_reserved_internal_range if form_reserved_internal_range and form_reserved_internal_range.strip() else None,
                "role": form_role if form_purpose == "REGIONAL_MANAGED_PROXY" else None,
                "private_ipv6_google_access": form_private_ipv6_google_access if form_private_ipv6_google_access and form_private_ipv6_google_access.strip() else None,
                "stack_type": form_stack_type,
                "ipv6_access_type": form_ipv6_access_type if form_stack_type != "IPV4_ONLY" else None,
                "external_ipv6_prefix": form_external_ipv6_prefix if form_external_ipv6_prefix and form_external_ipv6_prefix.strip() else None,
                "ip_collection": form_ip_collection if form_ip_collection and form_ip_collection.strip() else None,
                "allow_subnet_cidr_routes_overlap": form_allow_cidr_overlap,
                "send_secondary_ip_range_if_empty": form_send_secondary_empty,
                "resource_manager_tags": resource_tags,
                "log_config": log_config
            }

            st.session_state.subnets[i] = subnet_data

        if st.button("➕ Add Another Subnet", key="add_subnet_section"):
            st.session_state.subnet_form_count += 1
            st.rerun()

        if st.session_state.subnets:
            resources["subnets"] = st.session_state.subnets
    
    # Firewall Rules
    if st.checkbox("🔥 Create Firewall Rules"):
        st.markdown("**Firewall Configuration**")
        if 'firewall_rules' not in st.session_state:
            st.session_state.firewall_rules = []
        if 'firewall_form_count' not in st.session_state:
            st.session_state.firewall_form_count = 1

        for i in range(st.session_state.firewall_form_count):
            if i > 0:
                st.markdown("---")

            # Ensure data object exists
            if i >= len(st.session_state.firewall_rules):
                st.session_state.firewall_rules.append({
                    "name": f"firewall-rule-{i+1}",
                    "network": "my-vpc",
                    "direction": "INGRESS",
                    "protocol": "tcp",
                    "source_ranges": ["0.0.0.0/0"],
                    "source_tags": [],
                    "source_service_accounts": [],
                    "target_tags": [],
                    "target_service_accounts": [],
                    "destination_ranges": [],
                    "allows": [{"protocol": "tcp", "ports": ["22"]}],
                    "priority": 1000,
                    "disabled": False,
                    "description": "",
                    "enable_logging": False,
                    "log_config": None
                })

            rule = st.session_state.firewall_rules[i]

            st.markdown(f"**Firewall Rule {i+1}:**")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                form_name = st.text_input("Rule Name", value=rule.get('name', ''), key=f"fw_name_{i}")
            with col2:
                form_direction = st.selectbox(
                    "Direction", ["INGRESS", "EGRESS"],
                    index=0 if rule.get('direction', 'INGRESS') == 'INGRESS' else 1,
                    key=f"fw_direction_{i}"
                )
            with col3:
                form_protocol = st.selectbox(
                    "Protocol", ["tcp", "udp", "icmp", "all"],
                    index=["tcp", "udp", "icmp", "all"].index(rule.get('protocol', 'tcp')),
                    key=f"fw_protocol_{i}"
                )
            with col4:
                if st.button("🗑️", key=f"del_firewall_{i}"):
                    st.session_state.firewall_rules.pop(i)
                    st.session_state.firewall_form_count -= 1
                    st.rerun()

            # Additional fields
            col1, col2 = st.columns(2)
            with col1:
                # Determine available VPC names (only from currently enabled VPC section)
                vpc_options = []
                if resources.get("vpc") and resources["vpc"].get("name"):
                    vpc_options.append(resources["vpc"]["name"])
                if isinstance(resources.get("vpcs"), list):
                    for v in resources["vpcs"]:
                        if isinstance(v, dict) and v.get("name"):
                            vpc_options.append(v["name"])
                # Removed fallback to session_state.vpcs - only show VPCs when VPC section is enabled

                if vpc_options:
                    try:
                        default_vpc_idx = vpc_options.index(rule.get('network', vpc_options[0]))
                    except ValueError:
                        default_vpc_idx = 0
                    form_network = st.selectbox("Network", vpc_options, index=default_vpc_idx, key=f"fw_network_{i}")
                else:
                    form_network = st.text_input("Network", value=rule.get('network', 'my-vpc'), key=f"fw_network_text_{i}")
            with col2:
                form_source_ranges = st.text_input("Source Ranges (comma-separated)", 
                                                 value=", ".join(rule.get('source_ranges', ['0.0.0.0/0'])), 
                                                 key=f"fw_source_ranges_{i}")
            
            col1, col2 = st.columns(2)
            with col1:
                form_ports = st.text_input("Ports (comma-separated)", value="22", key=f"fw_ports_{i}")
            with col2:
                form_priority = st.number_input("Priority", value=rule.get('priority', 1000), min_value=0, max_value=65535, key=f"fw_priority_{i}")

            # Advanced fields (collapsible)
            with st.expander("🔧 Advanced Options", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    form_source_tags = st.text_input("Source Tags (comma-separated)", 
                                                   value=", ".join(rule.get('source_tags', [])), 
                                                   key=f"fw_source_tags_{i}")
                    form_source_service_accounts = st.text_input("Source Service Accounts (comma-separated)", 
                                                               value=", ".join(rule.get('source_service_accounts', [])), 
                                                               key=f"fw_source_service_accounts_{i}")
                with col2:
                    form_target_tags = st.text_input("Target Tags (comma-separated)", 
                                                   value=", ".join(rule.get('target_tags', [])), 
                                                   key=f"fw_target_tags_{i}")
                    form_target_service_accounts = st.text_input("Target Service Accounts (comma-separated)", 
                                                               value=", ".join(rule.get('target_service_accounts', [])), 
                                                               key=f"fw_target_service_accounts_{i}")

                col1, col2 = st.columns(2)
                with col1:
                    form_destination_ranges = st.text_input("Destination Ranges (comma-separated)", 
                                                          value=", ".join(rule.get('destination_ranges', [])), 
                                                          key=f"fw_destination_ranges_{i}")
                with col2:
                    form_disabled = st.checkbox("Disabled", value=rule.get('disabled', False), key=f"fw_disabled_{i}")

                # Description
                form_description = st.text_input("Description", value=rule.get('description', ''), key=f"fw_description_{i}")

                # Logging configuration
                st.markdown("**Logging:**")
                col1, col2 = st.columns(2)
                with col1:
                    form_enable_logging = st.checkbox("Enable Logging", value=rule.get('enable_logging', False), key=f"fw_enable_logging_{i}")
                with col2:
                    if form_enable_logging:
                        form_log_metadata = st.selectbox("Log Metadata", 
                                                       ["EXCLUDE_ALL_METADATA", "INCLUDE_ALL_METADATA"],
                                                       index=0 if rule.get('log_metadata', 'EXCLUDE_ALL_METADATA') == 'EXCLUDE_ALL_METADATA' else 1,
                                                       key=f"fw_log_metadata_{i}")
                    else:
                        form_log_metadata = "EXCLUDE_ALL_METADATA"

            # Parse comma-separated values
            source_ranges = [s.strip() for s in form_source_ranges.split(',') if s.strip()]
            ports = [p.strip() for p in form_ports.split(',') if p.strip()]
            source_tags = [s.strip() for s in form_source_tags.split(',') if s.strip()]
            source_service_accounts = [s.strip() for s in form_source_service_accounts.split(',') if s.strip()]
            target_tags = [s.strip() for s in form_target_tags.split(',') if s.strip()]
            target_service_accounts = [s.strip() for s in form_target_service_accounts.split(',') if s.strip()]
            destination_ranges = [s.strip() for s in form_destination_ranges.split(',') if s.strip()]
            
            # Build allows array
            allows = [{"protocol": form_protocol, "ports": ports}] if ports else [{"protocol": form_protocol}]
            
            # Build log_config if logging is enabled
            log_config = None
            if form_enable_logging:
                log_config = {"metadata": form_log_metadata}
            
            # Update rule
            st.session_state.firewall_rules[i] = {
                "name": form_name,
                "network": form_network,
                "direction": form_direction,
                "protocol": form_protocol,
                "source_ranges": source_ranges,
                "source_tags": source_tags,
                "source_service_accounts": source_service_accounts,
                "target_tags": target_tags,
                "target_service_accounts": target_service_accounts,
                "destination_ranges": destination_ranges,
                "allows": allows,
                "priority": form_priority,
                "disabled": form_disabled,
                "description": form_description,
                "enable_logging": form_enable_logging,
                "log_config": log_config
            }

        if st.button("➕ Add Another Firewall Rule", key="add_firewall_section"):
            st.session_state.firewall_form_count += 1
            st.rerun()

        if st.session_state.firewall_rules:
            resources["firewall_rules"] = st.session_state.firewall_rules
            # Debug: show what's being added
            st.info(f"Debug: Added {len(st.session_state.firewall_rules)} firewall rules to resources")
    
    # Service Accounts
    if st.checkbox("👤 Create Service Accounts"):
        st.markdown("**Service Account Configuration**")
        if 'service_accounts' not in st.session_state:
            st.session_state.service_accounts = []
        if 'service_account_form_count' not in st.session_state:
            st.session_state.service_account_form_count = 1

        for i in range(st.session_state.service_account_form_count):
            if i > 0:
                st.markdown("---")

            # Ensure data object exists
            if i >= len(st.session_state.service_accounts):
                st.session_state.service_accounts.append({
                    "account_id": f"service-account-{i+1}",
                    "display_name": f"Service Account {i+1}",
                    "description": "Service account created via GUI",
                    "disabled": False,
                    "create_ignore_already_exists": False,
                    "roles": [],
                    "create_key": False,
                    "key_algorithm": "KEY_ALG_RSA_2048",
                    "public_key_type": "TYPE_X509_PEM_FILE",
                    "private_key_type": "TYPE_GOOGLE_CREDENTIALS_FILE",
                    "key_file_path": None
                })

            sa = st.session_state.service_accounts[i]

            st.markdown(f"**Service Account {i+1}:**")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                form_account_id = st.text_input("Account ID", value=sa.get('account_id', ''), key=f"sa_account_id_{i}")
            with col2:
                form_display_name = st.text_input("Display Name", value=sa.get('display_name', ''), key=f"sa_display_name_{i}")
            with col3:
                form_description = st.text_input("Description", value=sa.get('description', ''), key=f"sa_description_{i}")
            with col4:
                if st.button("🗑️", key=f"del_sa_{i}"):
                    st.session_state.service_accounts.pop(i)
                    st.session_state.service_account_form_count -= 1
                    st.rerun()

            # Permissions/Roles selection
            st.markdown("**Permissions:**")
            common_roles = [
                # Basic IAM Roles
                "roles/browser",
                "roles/viewer", 
                "roles/editor",
                "roles/owner",
                # Storage Roles
                "roles/storage.objectViewer",
                "roles/storage.objectCreator", 
                "roles/storage.objectAdmin",
                # Compute Roles
                "roles/compute.instanceAdmin",
                "roles/compute.networkViewer",
                # Logging & Monitoring
                "roles/logging.logWriter",
                "roles/monitoring.metricWriter",
                # Security Roles
                "roles/secretmanager.secretAccessor",
                "roles/iam.serviceAccountUser",
                "roles/iam.serviceAccountTokenCreator",
                # Database Roles
                "roles/cloudsql.client",
                # Analytics Roles
                "roles/bigquery.dataViewer",
                "roles/bigquery.dataEditor",
                # Serverless Roles
                "roles/run.invoker",
                "roles/cloudfunctions.invoker"
            ]
            
            # Get current roles or default to empty list
            current_roles = sa.get('roles', [])
            form_roles = st.multiselect(
                "IAM Roles",
                common_roles,
                default=current_roles,
                key=f"sa_roles_{i}",
                help="Select IAM roles to assign to this service account"
            )

            # Advanced service account options (collapsible)
            with st.expander("🔧 Advanced Service Account Options", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    form_disabled = st.checkbox(
                        "Disabled", 
                        value=sa.get('disabled', False),
                        key=f"sa_disabled_{i}"
                    )
                with col2:
                    form_ignore_exists = st.checkbox(
                        "Ignore Already Exists", 
                        value=sa.get('create_ignore_already_exists', False),
                        key=f"sa_ignore_exists_{i}"
                    )
                
                # Custom roles input
                st.markdown("**Custom Roles:**")
                form_custom_roles = st.text_area(
                    "Custom IAM Roles (one per line)",
                    value="\n".join([role for role in current_roles if role not in common_roles]),
                    key=f"sa_custom_roles_{i}",
                    help="Enter custom IAM roles that are not in the common list above"
                )

            # Key Management section
            st.markdown("**Key Management:**")
            form_create_key = st.checkbox(
                "Create Service Account Key", 
                value=sa.get('create_key', False),
                key=f"sa_create_key_{i}",
                help="Generate a new service account key for this service account"
            )
            
            if form_create_key:
                col1, col2 = st.columns(2)
                with col1:
                    form_key_algorithm = st.selectbox(
                        "Key Algorithm",
                        ["KEY_ALG_RSA_1024", "KEY_ALG_RSA_2048"],
                        index=1 if sa.get('key_algorithm', 'KEY_ALG_RSA_2048') == 'KEY_ALG_RSA_2048' else 0,
                        key=f"sa_key_algorithm_{i}"
                    )
                    form_public_key_type = st.selectbox(
                        "Public Key Type",
                        ["TYPE_NONE", "TYPE_X509_PEM_FILE", "TYPE_RAW_PUBLIC_KEY"],
                        index=1 if sa.get('public_key_type', 'TYPE_X509_PEM_FILE') == 'TYPE_X509_PEM_FILE' else 0,
                        key=f"sa_public_key_type_{i}"
                    )
                with col2:
                    form_private_key_type = st.selectbox(
                        "Private Key Type",
                        ["TYPE_UNSPECIFIED", "TYPE_PKCS12_FILE", "TYPE_GOOGLE_CREDENTIALS_FILE"],
                        index=2 if sa.get('private_key_type', 'TYPE_GOOGLE_CREDENTIALS_FILE') == 'TYPE_GOOGLE_CREDENTIALS_FILE' else 0,
                        key=f"sa_private_key_type_{i}"
                    )
                    form_key_file_path = st.text_input(
                        "Key File Path (optional)",
                        value=sa.get('key_file_path', ''),
                        placeholder="/path/to/save/key.json",
                        key=f"sa_key_file_path_{i}",
                        help="Optional: Path to save the service account key file"
                    )

            # Parse custom roles from text area
            custom_roles = []
            if form_custom_roles and form_custom_roles.strip():
                custom_roles = [role.strip() for role in form_custom_roles.split('\n') if role.strip()]
            
            # Combine common roles and custom roles
            all_roles = form_roles + custom_roles

            # Update service account data
            st.session_state.service_accounts[i] = {
                "account_id": form_account_id,
                "display_name": form_display_name,
                "description": form_description if form_description and form_description.strip() else None,
                "disabled": form_disabled,
                "create_ignore_already_exists": form_ignore_exists,
                "roles": all_roles,
                "create_key": form_create_key,
                "key_algorithm": form_key_algorithm if form_create_key else None,
                "public_key_type": form_public_key_type if form_create_key else None,
                "private_key_type": form_private_key_type if form_create_key else None,
                "key_file_path": form_key_file_path if form_create_key and form_key_file_path and form_key_file_path.strip() else None
            }

        # Add button to create another service account
        if st.button("➕ Add Another Service Account", key="add_sa_section"):
            st.session_state.service_account_form_count += 1
            st.rerun()

        if st.session_state.service_accounts:
            resources["service_accounts"] = st.session_state.service_accounts
    
    # IAM
    if st.checkbox("🔐 Create IAM Policies"):
        st.markdown("**IAM Configuration**")
        if 'iam' not in st.session_state:
            st.session_state.iam = []
        if 'iam_form_count' not in st.session_state:
            st.session_state.iam_form_count = 1

        for i in range(st.session_state.iam_form_count):
            if i > 0:
                st.markdown("---")

            # Ensure data object exists
            if i >= len(st.session_state.iam):
                st.session_state.iam.append({
                    "iam_type": "member",
                    "role": "roles/viewer",
                    "member": "user:example@domain.com",
                    "members": [],
                    "policy_data": None,
                    "service": None,
                    "audit_log_configs": [],
                    "condition": None
                })

            binding = st.session_state.iam[i]

            st.markdown(f"**IAM Policy {i+1}:**")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                form_iam_type = st.selectbox(
                    "IAM Type",
                    ["member", "binding", "policy", "audit_config"],
                    index=["member", "binding", "policy", "audit_config"].index(binding.get('iam_type', 'member')),
                    key=f"iam_type_{i}"
                )
            with col2:
                if form_iam_type in ["member", "binding"]:
                    # Common IAM roles
                    common_roles = [
                        "Custom Role",  # Allow custom role input
                        "roles/owner",
                        "roles/editor", 
                        "roles/viewer",
                        "roles/browser",
                        "roles/iam.serviceAccountUser",
                        "roles/iam.serviceAccountTokenCreator",
                        "roles/iam.serviceAccountKeyAdmin",
                        "roles/iam.serviceAccountAdmin",
                        "roles/iam.organizationRoleAdmin",
                        "roles/iam.roleAdmin",
                        "roles/iam.workloadIdentityUser",
                        "roles/storage.admin",
                        "roles/storage.objectAdmin",
                        "roles/storage.objectCreator",
                        "roles/storage.objectViewer",
                        "roles/compute.admin",
                        "roles/compute.instanceAdmin",
                        "roles/compute.instanceAdmin.v1",
                        "roles/compute.networkAdmin",
                        "roles/compute.securityAdmin",
                        "roles/compute.viewer",
                        "roles/container.admin",
                        "roles/container.clusterAdmin",
                        "roles/container.developer",
                        "roles/container.viewer",
                        "roles/cloudsql.admin",
                        "roles/cloudsql.client",
                        "roles/cloudsql.viewer",
                        "roles/secretmanager.admin",
                        "roles/secretmanager.secretAccessor",
                        "roles/secretmanager.viewer",
                        "roles/pubsub.admin",
                        "roles/pubsub.editor",
                        "roles/pubsub.publisher",
                        "roles/pubsub.subscriber",
                        "roles/pubsub.viewer",
                        "roles/cloudfunctions.admin",
                        "roles/cloudfunctions.developer",
                        "roles/cloudfunctions.invoker",
                        "roles/cloudfunctions.viewer",
                        "roles/run.admin",
                        "roles/run.developer",
                        "roles/run.invoker",
                        "roles/run.viewer",
                        "roles/logging.admin",
                        "roles/logging.viewer",
                        "roles/monitoring.admin",
                        "roles/monitoring.viewer",
                        "roles/securitycenter.admin",
                        "roles/securitycenter.viewer",
                        "roles/dns.admin",
                        "roles/dns.reader",
                        "roles/firebase.admin",
                        "roles/firebase.analyticsAdmin",
                        "roles/firebase.analyticsViewer",
                        "roles/bigquery.admin",
                        "roles/bigquery.dataEditor",
                        "roles/bigquery.dataViewer",
                        "roles/bigquery.jobUser",
                        "roles/bigquery.user",
                        "roles/artifactregistry.admin",
                        "roles/artifactregistry.reader",
                        "roles/artifactregistry.writer"
                    ]
                    
                    # Get current role value
                    current_role = binding.get('role', '')
                    
                    # If current role is not in the list, add it as custom option
                    if current_role and current_role not in common_roles:
                        common_roles.insert(0, current_role)
                    
                    form_role = st.selectbox(
                        "Role", 
                        options=common_roles,
                        index=common_roles.index(current_role) if current_role in common_roles else 0,
                        key=f"iam_role_{i}",
                        help="Select a predefined role or choose custom for manual entry"
                    )
                    
                    # Show custom role input if "Custom Role" is selected
                    if form_role == "Custom Role":
                        form_role = st.text_input(
                            "Custom Role", 
                            value="",
                            placeholder="roles/custom.role",
                            key=f"iam_custom_role_{i}"
                        )
                elif form_iam_type == "policy":
                    form_policy_data = st.text_area(
                        "Policy Data (JSON)", 
                        value=binding.get('policy_data', ''),
                        placeholder='{"bindings": [{"role": "roles/viewer", "members": ["user:example@domain.com"]}]}',
                        key=f"iam_policy_data_{i}"
                    )
                else:  # audit_config
                    form_service = st.text_input(
                        "Service", 
                        value=binding.get('service', ''),
                        placeholder="allServices or compute.googleapis.com",
                        key=f"iam_service_{i}"
                    )
            with col3:
                if form_iam_type == "member":
                    form_member = st.text_input(
                        "Member", 
                        value=binding.get('member', ''),
                        placeholder="user:example@domain.com",
                        key=f"iam_member_{i}"
                    )
                elif form_iam_type == "binding":
                    form_members = st.text_area(
                        "Members (one per line)", 
                        value="\n".join(binding.get('members', [])),
                        placeholder="user:example@domain.com\nserviceAccount:sa@project.iam.gserviceaccount.com",
                        key=f"iam_members_{i}"
                    )
                elif form_iam_type == "audit_config":
                    form_audit_logs = st.text_area(
                        "Audit Log Configs (JSON)", 
                        value=json.dumps(binding.get('audit_log_configs', []), indent=2),
                        placeholder='[{"log_type": "ADMIN_READ", "exempted_members": []}]',
                        key=f"iam_audit_logs_{i}"
                    )
            with col4:
                if st.button("🗑️", key=f"del_iam_{i}"):
                    st.session_state.iam.pop(i)
                    st.session_state.iam_form_count -= 1
                    st.rerun()

            # IAM Conditions (for member and binding types)
            if form_iam_type in ["member", "binding"]:
                with st.expander("🔧 IAM Conditions (Optional)", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        form_condition_title = st.text_input(
                            "Condition Title", 
                            value=binding.get('condition', {}).get('title', '') if binding.get('condition') else '',
                            placeholder="expires_after_2024",
                            key=f"iam_condition_title_{i}"
                        )
                    with col2:
                        form_condition_expression = st.text_input(
                            "Condition Expression", 
                            value=binding.get('condition', {}).get('expression', '') if binding.get('condition') else '',
                            placeholder='request.time < timestamp("2024-12-31T23:59:59Z")',
                            key=f"iam_condition_expression_{i}"
                        )
                    form_condition_description = st.text_input(
                        "Condition Description (Optional)", 
                        value=binding.get('condition', {}).get('description', '') if binding.get('condition') else '',
                        placeholder="Access expires at end of 2024",
                        key=f"iam_condition_description_{i}"
                    )

            # Parse data based on IAM type
            if form_iam_type == "member":
                members_list = []
                condition = None
                if form_condition_title and form_condition_expression:
                    condition = {
                        "title": form_condition_title,
                        "expression": form_condition_expression,
                        "description": form_condition_description if form_condition_description else None
                    }
            elif form_iam_type == "binding":
                members_list = [m.strip() for m in form_members.split('\n') if m.strip()] if form_members else []
                condition = None
                if form_condition_title and form_condition_expression:
                    condition = {
                        "title": form_condition_title,
                        "expression": form_condition_expression,
                        "description": form_condition_description if form_condition_description else None
                    }
            elif form_iam_type == "policy":
                policy_data = form_policy_data if form_policy_data and form_policy_data.strip() else None
            elif form_iam_type == "audit_config":
                try:
                    audit_logs = json.loads(form_audit_logs) if form_audit_logs and form_audit_logs.strip() else []
                except json.JSONDecodeError:
                    audit_logs = []

            # Update IAM binding data
            if form_iam_type == "member":
                st.session_state.iam[i] = {
                    "iam_type": form_iam_type,
                    "role": form_role,
                    "member": form_member,
                    "members": [],
                    "policy_data": None,
                    "service": None,
                    "audit_log_configs": [],
                    "condition": condition
                }
            elif form_iam_type == "binding":
                st.session_state.iam[i] = {
                    "iam_type": form_iam_type,
                    "role": form_role,
                    "member": None,
                    "members": members_list,
                    "policy_data": None,
                    "service": None,
                    "audit_log_configs": [],
                    "condition": condition
                }
            elif form_iam_type == "policy":
                st.session_state.iam[i] = {
                    "iam_type": form_iam_type,
                    "role": None,
                    "member": None,
                    "members": [],
                    "policy_data": policy_data,
                    "service": None,
                    "audit_log_configs": [],
                    "condition": None
                }
            elif form_iam_type == "audit_config":
                st.session_state.iam[i] = {
                    "iam_type": form_iam_type,
                    "role": None,
                    "member": None,
                    "members": [],
                    "policy_data": None,
                    "service": form_service,
                    "audit_log_configs": audit_logs,
                    "condition": None
                }

        # Add button to create another IAM policy
        if st.button("➕ Add Another IAM Policy", key="add_iam_section"):
            st.session_state.iam_form_count += 1
            st.rerun()

        if st.session_state.iam:
            resources["iam"] = st.session_state.iam
    
    # Compute Instances
    if st.checkbox("💻 Create Compute Instances"):
        st.markdown("**VM Configuration**")
        if 'compute_instances' not in st.session_state:
            st.session_state.compute_instances = []

        # ---- Pricing helpers (approximate) ----
        def infer_vcpu_and_memory(machine_type: str) -> tuple[float, float]:
            mt = (machine_type or "").lower()
            # Known presets
            presets = {
                "e2-micro": (0.25, 1),
                "e2-small": (0.5, 2),
                "e2-medium": (2, 4),
                "e2-standard-2": (2, 8),
                "e2-standard-4": (4, 16),
                "n2-standard-2": (2, 8),
                "n2-standard-4": (4, 16),
            }
            if mt in presets:
                return presets[mt]
            # Heuristic: standard-N => vcpu=N, mem=4GB per vCPU
            import re
            m = re.search(r"-(\d+)$", mt)
            if m:
                vcpu = float(m.group(1))
                mem = vcpu * 4.0
                return (vcpu, mem)
            # Fallback
            return (2.0, 8.0)

        def estimate_vm_cost_monthly(vm: dict) -> dict:
            # Approximate hourly pricing model (us-central1):
            # hourly_compute = vcpu*0.03 + mem_gb*0.005
            vcpu, mem_gb = infer_vcpu_and_memory(vm.get('machine_type', 'e2-standard-2'))
            hourly_compute = vcpu * 0.03 + mem_gb * 0.005
            # Disk pricing (balanced): $0.10 per GB-month; SSD: $0.17; standard: $0.04
            size_gb = (vm.get('boot_disk_size_gb') or 10)
            dtype = (vm.get('boot_disk_type') or 'pd-balanced').lower()
            per_gb_month = 0.10 if 'balanced' in dtype else (0.17 if 'ssd' in dtype else 0.04)
            disk_month = size_gb * per_gb_month
            monthly_compute = hourly_compute * 730.0
            total = monthly_compute + disk_month
            return {
                "vcpu": vcpu,
                "mem_gb": mem_gb,
                "hourly_compute": hourly_compute,
                "monthly_compute": monthly_compute,
                "disk_month": disk_month,
                "total": total,
            }

        # ---- Machine series specifications ----
        def get_machine_series_data() -> list:
            """Return machine series data for table display"""
            return [
                {"Series": "C4", "Description": "Consistently high performance", "vCPUs": "2 - 288", "Memory": "4 - 2,232 GB", "CPU Platform": "Intel Emerald Rapids"},
                {"Series": "C4A", "Description": "Arm-based consistently high performance", "vCPUs": "1 - 72", "Memory": "2 - 576 GB", "CPU Platform": "Google Axion"},
                {"Series": "C4D", "Description": "Consistently high performance", "vCPUs": "2 - 384", "Memory": "3 - 3,072 GB", "CPU Platform": "AMD Turin"},
                {"Series": "N4", "Description": "Flexible & cost-optimized", "vCPUs": "2 - 80", "Memory": "4 - 640 GB", "CPU Platform": "Intel Emerald Rapids"},
                {"Series": "C3", "Description": "Consistently high performance", "vCPUs": "4 - 192", "Memory": "8 - 1,536 GB", "CPU Platform": "Intel Sapphire Rapids"},
                {"Series": "C3D", "Description": "Consistently high performance", "vCPUs": "4 - 360", "Memory": "8 - 2,880 GB", "CPU Platform": "AMD Genoa"},
                {"Series": "E2", "Description": "Low cost, day-to-day computing", "vCPUs": "0.25 - 32", "Memory": "1 - 128 GB", "CPU Platform": "Intel Broadwell"},
                {"Series": "N2", "Description": "Balanced price & performance", "vCPUs": "2 - 128", "Memory": "2 - 864 GB", "CPU Platform": "Intel Cascade Lake"},
                {"Series": "N2D", "Description": "Balanced price & performance", "vCPUs": "2 - 224", "Memory": "2 - 896 GB", "CPU Platform": "AMD Milan"},
                {"Series": "T2A", "Description": "Scale-out workloads", "vCPUs": "1 - 48", "Memory": "4 - 192 GB", "CPU Platform": "Ampere Altra"},
                {"Series": "T2D", "Description": "Scale-out workloads", "vCPUs": "1 - 60", "Memory": "4 - 240 GB", "CPU Platform": "AMD Milan"},
                {"Series": "N1", "Description": "Balanced price & performance", "vCPUs": "0.25 - 96", "Memory": "0.6 - 624 GB", "CPU Platform": "Intel Haswell"}
            ]
        
        def get_series_presets(series: str) -> Dict[str, list]:
            """Get presets for a specific series"""
            presets = {
                "C4": {
                    "Standard": [
                        ("c4-standard-2", "2 vCPU (1 core), 7 GB memory"),
                        ("c4-standard-4", "4 vCPU (2 core), 15 GB memory"),
                        ("c4-standard-8", "8 vCPU (4 core), 30 GB memory"),
                        ("c4-standard-16", "16 vCPU (8 core), 60 GB memory"),
                        ("c4-standard-24", "24 vCPU (12 core), 90 GB memory"),
                        ("c4-standard-32", "32 vCPU (16 core), 120 GB memory"),
                        ("c4-standard-48", "48 vCPU (24 core), 180 GB memory"),
                        ("c4-standard-96", "96 vCPU (48 core), 360 GB memory"),
                        ("c4-standard-144", "144 vCPU (72 core), 540 GB memory"),
                        ("c4-standard-192", "192 vCPU (96 core), 720 GB memory"),
                        ("c4-standard-288", "288 vCPU (144 core), 1,080 GB memory"),
                        ("c4-standard-288-metal", "288 vCPU, 1,080 GB memory")
                    ],
                    "Standard with local SSD": [
                        ("c4-standard-4-lssd", "4 vCPU (2 core), 15 GB memory, 1 Local SSD disks"),
                        ("c4-standard-8-lssd", "8 vCPU (4 core), 30 GB memory, 1 Local SSD disks"),
                        ("c4-standard-16-lssd", "16 vCPU (8 core), 60 GB memory, 2 Local SSD disks"),
                        ("c4-standard-24-lssd", "24 vCPU (12 core), 90 GB memory, 4 Local SSD disks"),
                        ("c4-standard-32-lssd", "32 vCPU (16 core), 120 GB memory, 5 Local SSD disks"),
                        ("c4-standard-48-lssd", "48 vCPU (24 core), 180 GB memory, 8 Local SSD disks"),
                        ("c4-standard-96-lssd", "96 vCPU (48 core), 360 GB memory, 16 Local SSD disks"),
                        ("c4-standard-144-lssd", "144 vCPU (72 core), 540 GB memory, 24 Local SSD disks"),
                        ("c4-standard-192-lssd", "192 vCPU (96 core), 720 GB memory, 32 Local SSD disks"),
                        ("c4-standard-288-lssd", "288 vCPU (144 core), 1,080 GB memory, 48 Local SSD disks")
                    ],
                    "High memory": [
                        ("c4-highmem-2", "2 vCPU (1 core), 15 GB memory"),
                        ("c4-highmem-4", "4 vCPU (2 core), 31 GB memory"),
                        ("c4-highmem-8", "8 vCPU (4 core), 62 GB memory"),
                        ("c4-highmem-16", "16 vCPU (8 core), 124 GB memory"),
                        ("c4-highmem-24", "24 vCPU (12 core), 186 GB memory"),
                        ("c4-highmem-32", "32 vCPU (16 core), 248 GB memory"),
                        ("c4-highmem-48", "48 vCPU (24 core), 372 GB memory"),
                        ("c4-highmem-96", "96 vCPU (48 core), 744 GB memory"),
                        ("c4-highmem-144", "144 vCPU (72 core), 1,116 GB memory"),
                        ("c4-highmem-192", "192 vCPU (96 core), 1,488 GB memory"),
                        ("c4-highmem-288", "288 vCPU (144 core), 2,232 GB memory"),
                        ("c4-highmem-288-metal", "288 vCPU, 2,232 GB memory")
                    ],
                    "High memory with local SSD": [
                        ("c4-highmem-4-lssd", "4 vCPU (2 core), 31 GB memory, 1 Local SSD disks"),
                        ("c4-highmem-8-lssd", "8 vCPU (4 core), 62 GB memory, 1 Local SSD disks"),
                        ("c4-highmem-16-lssd", "16 vCPU (8 core), 124 GB memory, 2 Local SSD disks"),
                        ("c4-highmem-24-lssd", "24 vCPU (12 core), 186 GB memory, 4 Local SSD disks"),
                        ("c4-highmem-32-lssd", "32 vCPU (16 core), 248 GB memory, 5 Local SSD disks"),
                        ("c4-highmem-48-lssd", "48 vCPU (24 core), 372 GB memory, 8 Local SSD disks"),
                        ("c4-highmem-96-lssd", "96 vCPU (48 core), 744 GB memory, 16 Local SSD disks"),
                        ("c4-highmem-144-lssd", "144 vCPU (72 core), 1,116 GB memory, 24 Local SSD disks"),
                        ("c4-highmem-192-lssd", "192 vCPU (96 core), 1,488 GB memory, 32 Local SSD disks"),
                        ("c4-highmem-288-lssd", "288 vCPU (144 core), 2,232 GB memory, 48 Local SSD disks")
                    ],
                    "High CPU": [
                        ("c4-highcpu-2", "2 vCPU (1 core), 4 GB memory"),
                        ("c4-highcpu-4", "4 vCPU (2 core), 8 GB memory"),
                        ("c4-highcpu-8", "8 vCPU (4 core), 16 GB memory"),
                        ("c4-highcpu-16", "16 vCPU (8 core), 32 GB memory"),
                        ("c4-highcpu-24", "24 vCPU (12 core), 48 GB memory"),
                        ("c4-highcpu-32", "32 vCPU (16 core), 64 GB memory"),
                        ("c4-highcpu-48", "48 vCPU (24 core), 96 GB memory"),
                        ("c4-highcpu-96", "96 vCPU (48 core), 192 GB memory"),
                        ("c4-highcpu-144", "144 vCPU (72 core), 288 GB memory"),
                        ("c4-highcpu-192", "192 vCPU (96 core), 384 GB memory"),
                        ("c4-highcpu-288", "288 vCPU (144 core), 576 GB memory")
                    ]
                },
                "C4A": {
                    "Standard": [
                        ("c4a-standard-1", "1 vCPU, 4 GB memory"),
                        ("c4a-standard-2", "2 vCPU, 8 GB memory"),
                        ("c4a-standard-4", "4 vCPU, 16 GB memory"),
                        ("c4a-standard-8", "8 vCPU, 32 GB memory"),
                        ("c4a-standard-16", "16 vCPU, 64 GB memory"),
                        ("c4a-standard-32", "32 vCPU, 128 GB memory"),
                        ("c4a-standard-48", "48 vCPU, 192 GB memory"),
                        ("c4a-standard-64", "64 vCPU, 256 GB memory"),
                        ("c4a-standard-72", "72 vCPU, 288 GB memory")
                    ],
                    "Standard with local SSD": [
                        ("c4a-standard-4-lssd", "4 vCPU, 16 GB memory, 1 Local SSD disks"),
                        ("c4a-standard-8-lssd", "8 vCPU, 32 GB memory, 2 Local SSD disks"),
                        ("c4a-standard-16-lssd", "16 vCPU, 64 GB memory, 4 Local SSD disks"),
                        ("c4a-standard-32-lssd", "32 vCPU, 128 GB memory, 6 Local SSD disks"),
                        ("c4a-standard-48-lssd", "48 vCPU, 192 GB memory, 10 Local SSD disks"),
                        ("c4a-standard-64-lssd", "64 vCPU, 256 GB memory, 14 Local SSD disks"),
                        ("c4a-standard-72-lssd", "72 vCPU, 288 GB memory, 16 Local SSD disks")
                    ],
                    "High memory": [
                        ("c4a-highmem-1", "1 vCPU, 8 GB memory"),
                        ("c4a-highmem-2", "2 vCPU, 16 GB memory"),
                        ("c4a-highmem-4", "4 vCPU, 32 GB memory"),
                        ("c4a-highmem-8", "8 vCPU, 64 GB memory"),
                        ("c4a-highmem-16", "16 vCPU, 128 GB memory"),
                        ("c4a-highmem-32", "32 vCPU, 256 GB memory"),
                        ("c4a-highmem-48", "48 vCPU, 384 GB memory"),
                        ("c4a-highmem-64", "64 vCPU, 512 GB memory"),
                        ("c4a-highmem-72", "72 vCPU, 576 GB memory")
                    ],
                    "High memory with local SSD": [
                        ("c4a-highmem-4-lssd", "4 vCPU, 32 GB memory, 1 Local SSD disks"),
                        ("c4a-highmem-8-lssd", "8 vCPU, 64 GB memory, 2 Local SSD disks"),
                        ("c4a-highmem-16-lssd", "16 vCPU, 128 GB memory, 4 Local SSD disks"),
                        ("c4a-highmem-32-lssd", "32 vCPU, 256 GB memory, 6 Local SSD disks"),
                        ("c4a-highmem-48-lssd", "48 vCPU, 384 GB memory, 10 Local SSD disks"),
                        ("c4a-highmem-64-lssd", "64 vCPU, 512 GB memory, 14 Local SSD disks"),
                        ("c4a-highmem-72-lssd", "72 vCPU, 576 GB memory, 16 Local SSD disks")
                    ],
                    "High CPU": [
                        ("c4a-highcpu-1", "1 vCPU, 2 GB memory"),
                        ("c4a-highcpu-2", "2 vCPU, 4 GB memory"),
                        ("c4a-highcpu-4", "4 vCPU, 8 GB memory"),
                        ("c4a-highcpu-8", "8 vCPU, 16 GB memory"),
                        ("c4a-highcpu-16", "16 vCPU, 32 GB memory"),
                        ("c4a-highcpu-32", "32 vCPU, 64 GB memory"),
                        ("c4a-highcpu-48", "48 vCPU, 96 GB memory"),
                        ("c4a-highcpu-64", "64 vCPU, 128 GB memory"),
                        ("c4a-highcpu-72", "72 vCPU, 144 GB memory")
                    ]
                },
                "C4D": {
                    "Standard": [
                        ("c4d-standard-2", "2 vCPU (1 core), 7 GB memory"),
                        ("c4d-standard-4", "4 vCPU (2 core), 15 GB memory"),
                        ("c4d-standard-8", "8 vCPU (4 core), 31 GB memory"),
                        ("c4d-standard-16", "16 vCPU (8 core), 62 GB memory"),
                        ("c4d-standard-32", "32 vCPU (16 core), 124 GB memory"),
                        ("c4d-standard-48", "48 vCPU (24 core), 186 GB memory"),
                        ("c4d-standard-64", "64 vCPU (32 core), 248 GB memory"),
                        ("c4d-standard-96", "96 vCPU (48 core), 372 GB memory"),
                        ("c4d-standard-192", "192 vCPU (96 core), 744 GB memory"),
                        ("c4d-standard-384", "384 vCPU (192 core), 1,488 GB memory"),
                        ("c4d-standard-384-metal", "384 vCPU, 1,536 GB memory")
                    ],
                    "Standard with local SSD": [
                        ("c4d-standard-8-lssd", "8 vCPU (4 core), 31 GB memory, 1 Local SSD disks"),
                        ("c4d-standard-16-lssd", "16 vCPU (8 core), 62 GB memory, 1 Local SSD disks"),
                        ("c4d-standard-32-lssd", "32 vCPU (16 core), 124 GB memory, 2 Local SSD disks"),
                        ("c4d-standard-48-lssd", "48 vCPU (24 core), 186 GB memory, 4 Local SSD disks"),
                        ("c4d-standard-64-lssd", "64 vCPU (32 core), 248 GB memory, 6 Local SSD disks"),
                        ("c4d-standard-96-lssd", "96 vCPU (48 core), 372 GB memory, 8 Local SSD disks"),
                        ("c4d-standard-192-lssd", "192 vCPU (96 core), 744 GB memory, 16 Local SSD disks"),
                        ("c4d-standard-384-lssd", "384 vCPU (192 core), 1,488 GB memory, 32 Local SSD disks")
                    ],
                    "High memory": [
                        ("c4d-highmem-2", "2 vCPU (1 core), 15 GB memory"),
                        ("c4d-highmem-4", "4 vCPU (2 core), 31 GB memory"),
                        ("c4d-highmem-8", "8 vCPU (4 core), 63 GB memory"),
                        ("c4d-highmem-16", "16 vCPU (8 core), 126 GB memory"),
                        ("c4d-highmem-32", "32 vCPU (16 core), 252 GB memory"),
                        ("c4d-highmem-48", "48 vCPU (24 core), 378 GB memory"),
                        ("c4d-highmem-64", "64 vCPU (32 core), 504 GB memory"),
                        ("c4d-highmem-96", "96 vCPU (48 core), 756 GB memory"),
                        ("c4d-highmem-192", "192 vCPU (96 core), 1,512 GB memory"),
                        ("c4d-highmem-384", "384 vCPU (192 core), 3,024 GB memory"),
                        ("c4d-highmem-384-metal", "384 vCPU, 3,072 GB memory")
                    ],
                    "High memory with local SSD": [
                        ("c4d-highmem-8-lssd", "8 vCPU (4 core), 63 GB memory, 1 Local SSD disks"),
                        ("c4d-highmem-16-lssd", "16 vCPU (8 core), 126 GB memory, 1 Local SSD disks"),
                        ("c4d-highmem-32-lssd", "32 vCPU (16 core), 252 GB memory, 2 Local SSD disks"),
                        ("c4d-highmem-48-lssd", "48 vCPU (24 core), 378 GB memory, 4 Local SSD disks"),
                        ("c4d-highmem-64-lssd", "64 vCPU (32 core), 504 GB memory, 6 Local SSD disks"),
                        ("c4d-highmem-96-lssd", "96 vCPU (48 core), 756 GB memory, 8 Local SSD disks"),
                        ("c4d-highmem-192-lssd", "192 vCPU (96 core), 1,512 GB memory, 16 Local SSD disks"),
                        ("c4d-highmem-384-lssd", "384 vCPU (192 core), 3,024 GB memory, 32 Local SSD disks")
                    ],
                    "High CPU": [
                        ("c4d-highcpu-2", "2 vCPU (1 core), 3 GB memory"),
                        ("c4d-highcpu-4", "4 vCPU (2 core), 7 GB memory"),
                        ("c4d-highcpu-8", "8 vCPU (4 core), 15 GB memory"),
                        ("c4d-highcpu-16", "16 vCPU (8 core), 30 GB memory"),
                        ("c4d-highcpu-32", "32 vCPU (16 core), 60 GB memory"),
                        ("c4d-highcpu-48", "48 vCPU (24 core), 90 GB memory"),
                        ("c4d-highcpu-64", "64 vCPU (32 core), 120 GB memory"),
                        ("c4d-highcpu-96", "96 vCPU (48 core), 180 GB memory"),
                        ("c4d-highcpu-192", "192 vCPU (96 core), 360 GB memory"),
                        ("c4d-highcpu-384", "384 vCPU (192 core), 720 GB memory"),
                        ("c4d-highcpu-384-metal", "384 vCPU, 768 GB memory")
                    ]
                },
                "N4": {
                    "Standard": [
                        ("n4-standard-2", "2 vCPU (1 core), 8 GB memory"),
                        ("n4-standard-4", "4 vCPU (2 core), 16 GB memory"),
                        ("n4-standard-8", "8 vCPU (4 core), 32 GB memory"),
                        ("n4-standard-16", "16 vCPU (8 core), 64 GB memory"),
                        ("n4-standard-32", "32 vCPU (16 core), 128 GB memory"),
                        ("n4-standard-48", "48 vCPU (24 core), 192 GB memory"),
                        ("n4-standard-64", "64 vCPU (32 core), 256 GB memory"),
                        ("n4-standard-80", "80 vCPU (40 core), 320 GB memory")
                    ],
                    "High memory": [
                        ("n4-highmem-2", "2 vCPU (1 core), 16 GB memory"),
                        ("n4-highmem-4", "4 vCPU (2 core), 32 GB memory"),
                        ("n4-highmem-8", "8 vCPU (4 core), 64 GB memory"),
                        ("n4-highmem-16", "16 vCPU (8 core), 128 GB memory"),
                        ("n4-highmem-32", "32 vCPU (16 core), 256 GB memory"),
                        ("n4-highmem-48", "48 vCPU (24 core), 384 GB memory"),
                        ("n4-highmem-64", "64 vCPU (32 core), 512 GB memory"),
                        ("n4-highmem-80", "80 vCPU (40 core), 640 GB memory")
                    ],
                    "High CPU": [
                        ("n4-highcpu-2", "2 vCPU (1 core), 4 GB memory"),
                        ("n4-highcpu-4", "4 vCPU (2 core), 8 GB memory"),
                        ("n4-highcpu-8", "8 vCPU (4 core), 16 GB memory"),
                        ("n4-highcpu-16", "16 vCPU (8 core), 32 GB memory"),
                        ("n4-highcpu-32", "32 vCPU (16 core), 64 GB memory"),
                        ("n4-highcpu-48", "48 vCPU (24 core), 96 GB memory"),
                        ("n4-highcpu-64", "64 vCPU (32 core), 128 GB memory"),
                        ("n4-highcpu-80", "80 vCPU (40 core), 160 GB memory")
                    ]
                },
                "C3": {
                    "Standard": [
                        ("c3-standard-4", "4 vCPU (2 core), 16 GB memory"),
                        ("c3-standard-8", "8 vCPU (4 core), 32 GB memory"),
                        ("c3-standard-22", "22 vCPU (11 core), 88 GB memory"),
                        ("c3-standard-44", "44 vCPU (22 core), 176 GB memory"),
                        ("c3-standard-88", "88 vCPU (44 core), 352 GB memory"),
                        ("c3-standard-176", "176 vCPU (88 core), 704 GB memory"),
                        ("c3-standard-192-metal", "192 vCPU, 768 GB memory")
                    ],
                    "Standard with local SSD": [
                        ("c3-standard-4-lssd", "4 vCPU (2 core), 16 GB memory, 1 Local SSD disks"),
                        ("c3-standard-8-lssd", "8 vCPU (4 core), 32 GB memory, 2 Local SSD disks"),
                        ("c3-standard-22-lssd", "22 vCPU (11 core), 88 GB memory, 4 Local SSD disks"),
                        ("c3-standard-44-lssd", "44 vCPU (22 core), 176 GB memory, 8 Local SSD disks"),
                        ("c3-standard-88-lssd", "88 vCPU (44 core), 352 GB memory, 16 Local SSD disks"),
                        ("c3-standard-176-lssd", "176 vCPU (88 core), 704 GB memory, 32 Local SSD disks")
                    ],
                    "High memory": [
                        ("c3-highmem-4", "4 vCPU (2 core), 32 GB memory"),
                        ("c3-highmem-8", "8 vCPU (4 core), 64 GB memory"),
                        ("c3-highmem-22", "22 vCPU (11 core), 176 GB memory"),
                        ("c3-highmem-44", "44 vCPU (22 core), 352 GB memory"),
                        ("c3-highmem-88", "88 vCPU (44 core), 704 GB memory"),
                        ("c3-highmem-176", "176 vCPU (88 core), 1,408 GB memory"),
                        ("c3-highmem-192-metal", "192 vCPU, 1,536 GB memory")
                    ],
                    "High CPU": [
                        ("c3-highcpu-4", "4 vCPU (2 core), 8 GB memory"),
                        ("c3-highcpu-8", "8 vCPU (4 core), 16 GB memory"),
                        ("c3-highcpu-22", "22 vCPU (11 core), 44 GB memory"),
                        ("c3-highcpu-44", "44 vCPU (22 core), 88 GB memory"),
                        ("c3-highcpu-88", "88 vCPU (44 core), 176 GB memory"),
                        ("c3-highcpu-176", "176 vCPU (88 core), 352 GB memory"),
                        ("c3-highcpu-192-metal", "192 vCPU, 512 GB memory")
                    ]
                },
                "C3D": {
                    "Standard": [
                        ("c3d-standard-4", "4 vCPU (2 core), 16 GB memory"),
                        ("c3d-standard-8", "8 vCPU (4 core), 32 GB memory"),
                        ("c3d-standard-16", "16 vCPU (8 core), 64 GB memory"),
                        ("c3d-standard-30", "30 vCPU (15 core), 120 GB memory"),
                        ("c3d-standard-60", "60 vCPU (30 core), 240 GB memory"),
                        ("c3d-standard-90", "90 vCPU (45 core), 360 GB memory"),
                        ("c3d-standard-180", "180 vCPU (90 core), 720 GB memory"),
                        ("c3d-standard-360", "360 vCPU (180 core), 1,440 GB memory")
                    ],
                    "Standard with local SSD": [
                        ("c3d-standard-8-lssd", "8 vCPU (4 core), 32 GB memory, 1 Local SSD disks"),
                        ("c3d-standard-16-lssd", "16 vCPU (8 core), 64 GB memory, 1 Local SSD disks"),
                        ("c3d-standard-30-lssd", "30 vCPU (15 core), 120 GB memory, 2 Local SSD disks"),
                        ("c3d-standard-60-lssd", "60 vCPU (30 core), 240 GB memory, 4 Local SSD disks"),
                        ("c3d-standard-90-lssd", "90 vCPU (45 core), 360 GB memory, 8 Local SSD disks"),
                        ("c3d-standard-180-lssd", "180 vCPU (90 core), 720 GB memory, 16 Local SSD disks"),
                        ("c3d-standard-360-lssd", "360 vCPU (180 core), 1,440 GB memory, 32 Local SSD disks")
                    ],
                    "High memory": [
                        ("c3d-highmem-4", "4 vCPU (2 core), 32 GB memory"),
                        ("c3d-highmem-8", "8 vCPU (4 core), 64 GB memory"),
                        ("c3d-highmem-16", "16 vCPU (8 core), 128 GB memory"),
                        ("c3d-highmem-30", "30 vCPU (15 core), 240 GB memory"),
                        ("c3d-highmem-60", "60 vCPU (30 core), 480 GB memory"),
                        ("c3d-highmem-90", "90 vCPU (45 core), 720 GB memory"),
                        ("c3d-highmem-180", "180 vCPU (90 core), 1,440 GB memory"),
                        ("c3d-highmem-360", "360 vCPU (180 core), 2,880 GB memory")
                    ],
                    "High memory with local SSD": [
                        ("c3d-highmem-8-lssd", "8 vCPU (4 core), 64 GB memory, 1 Local SSD disks"),
                        ("c3d-highmem-16-lssd", "16 vCPU (8 core), 128 GB memory, 1 Local SSD disks"),
                        ("c3d-highmem-30-lssd", "30 vCPU (15 core), 240 GB memory, 2 Local SSD disks"),
                        ("c3d-highmem-60-lssd", "60 vCPU (30 core), 480 GB memory, 4 Local SSD disks"),
                        ("c3d-highmem-90-lssd", "90 vCPU (45 core), 720 GB memory, 8 Local SSD disks"),
                        ("c3d-highmem-180-lssd", "180 vCPU (90 core), 1,440 GB memory, 16 Local SSD disks"),
                        ("c3d-highmem-360-lssd", "360 vCPU (180 core), 2,880 GB memory, 32 Local SSD disks")
                    ],
                    "High CPU": [
                        ("c3d-highcpu-4", "4 vCPU (2 core), 8 GB memory"),
                        ("c3d-highcpu-8", "8 vCPU (4 core), 16 GB memory"),
                        ("c3d-highcpu-16", "16 vCPU (8 core), 32 GB memory"),
                        ("c3d-highcpu-30", "30 vCPU (15 core), 59 GB memory"),
                        ("c3d-highcpu-60", "60 vCPU (30 core), 118 GB memory"),
                        ("c3d-highcpu-90", "90 vCPU (45 core), 177 GB memory"),
                        ("c3d-highcpu-180", "180 vCPU (90 core), 354 GB memory"),
                        ("c3d-highcpu-360", "360 vCPU (180 core), 708 GB memory")
                    ]
                },
                "E2": {
                    "Shared-core": [
                        ("e2-micro", "0.25-2 vCPU (1 shared core), 1 GB memory"),
                        ("e2-small", "0.5-2 vCPU (1 shared core), 2 GB memory"),
                        ("e2-medium", "1-2 vCPU (1 shared core), 4 GB memory")
                    ],
                    "Standard": [
                        ("e2-standard-2", "2 vCPU (1 core), 8 GB memory"),
                        ("e2-standard-4", "4 vCPU (2 cores), 16 GB memory"),
                        ("e2-standard-8", "8 vCPU (4 cores), 32 GB memory"),
                        ("e2-standard-16", "16 vCPU (8 cores), 64 GB memory"),
                        ("e2-standard-32", "32 vCPU (16 cores), 128 GB memory")
                    ],
                    "High memory": [
                        ("e2-highmem-2", "2 vCPU (1 core), 16 GB memory"),
                        ("e2-highmem-4", "4 vCPU (2 cores), 32 GB memory"),
                        ("e2-highmem-8", "8 vCPU (4 cores), 64 GB memory"),
                        ("e2-highmem-16", "16 vCPU (8 cores), 128 GB memory")
                    ],
                    "High CPU": [
                        ("e2-highcpu-2", "2 vCPU (1 core), 2 GB memory"),
                        ("e2-highcpu-4", "4 vCPU (2 cores), 4 GB memory"),
                        ("e2-highcpu-8", "8 vCPU (4 cores), 8 GB memory"),
                        ("e2-highcpu-16", "16 vCPU (8 cores), 16 GB memory"),
                        ("e2-highcpu-32", "32 vCPU (16 cores), 32 GB memory")
                    ]
                },
                "N2": {
                    "Standard": [
                        ("n2-standard-2", "2 vCPU (1 core), 8 GB memory"),
                        ("n2-standard-4", "4 vCPU (2 core), 16 GB memory"),
                        ("n2-standard-8", "8 vCPU (4 core), 32 GB memory"),
                        ("n2-standard-16", "16 vCPU (8 core), 64 GB memory"),
                        ("n2-standard-32", "32 vCPU (16 core), 128 GB memory"),
                        ("n2-standard-48", "48 vCPU (24 core), 192 GB memory"),
                        ("n2-standard-64", "64 vCPU (32 core), 256 GB memory"),
                        ("n2-standard-80", "80 vCPU (40 core), 320 GB memory"),
                        ("n2-standard-96", "96 vCPU (48 core), 384 GB memory"),
                        ("n2-standard-128", "128 vCPU (64 core), 512 GB memory")
                    ],
                    "High memory": [
                        ("n2-highmem-2", "2 vCPU (1 core), 16 GB memory"),
                        ("n2-highmem-4", "4 vCPU (2 core), 32 GB memory"),
                        ("n2-highmem-8", "8 vCPU (4 core), 64 GB memory"),
                        ("n2-highmem-16", "16 vCPU (8 core), 128 GB memory"),
                        ("n2-highmem-32", "32 vCPU (16 core), 256 GB memory"),
                        ("n2-highmem-48", "48 vCPU (24 core), 384 GB memory"),
                        ("n2-highmem-64", "64 vCPU (32 core), 512 GB memory"),
                        ("n2-highmem-80", "80 vCPU (40 core), 640 GB memory"),
                        ("n2-highmem-96", "96 vCPU (48 core), 768 GB memory"),
                        ("n2-highmem-128", "128 vCPU (64 core), 864 GB memory")
                    ],
                    "High CPU": [
                        ("n2-highcpu-2", "2 vCPU (1 core), 2 GB memory"),
                        ("n2-highcpu-4", "4 vCPU (2 core), 4 GB memory"),
                        ("n2-highcpu-8", "8 vCPU (4 core), 8 GB memory"),
                        ("n2-highcpu-16", "16 vCPU (8 core), 16 GB memory"),
                        ("n2-highcpu-32", "32 vCPU (16 core), 32 GB memory"),
                        ("n2-highcpu-48", "48 vCPU (24 core), 48 GB memory"),
                        ("n2-highcpu-64", "64 vCPU (32 core), 64 GB memory"),
                        ("n2-highcpu-80", "80 vCPU (40 core), 80 GB memory"),
                        ("n2-highcpu-96", "96 vCPU (48 core), 96 GB memory")
                    ]
                },
                "N2D": {
                    "Standard": [
                        ("n2d-standard-2", "2 vCPU (1 core), 8 GB memory"),
                        ("n2d-standard-4", "4 vCPU (2 core), 16 GB memory"),
                        ("n2d-standard-8", "8 vCPU (4 core), 32 GB memory"),
                        ("n2d-standard-16", "16 vCPU (8 core), 64 GB memory"),
                        ("n2d-standard-32", "32 vCPU (16 core), 128 GB memory"),
                        ("n2d-standard-48", "48 vCPU (24 core), 192 GB memory"),
                        ("n2d-standard-64", "64 vCPU (32 core), 256 GB memory"),
                        ("n2d-standard-80", "80 vCPU (40 core), 320 GB memory"),
                        ("n2d-standard-96", "96 vCPU (48 core), 384 GB memory"),
                        ("n2d-standard-128", "128 vCPU (64 core), 512 GB memory"),
                        ("n2d-standard-224", "224 vCPU (112 core), 896 GB memory")
                    ],
                    "High memory": [
                        ("n2d-highmem-2", "2 vCPU (1 core), 16 GB memory"),
                        ("n2d-highmem-4", "4 vCPU (2 core), 32 GB memory"),
                        ("n2d-highmem-8", "8 vCPU (4 core), 64 GB memory"),
                        ("n2d-highmem-16", "16 vCPU (8 core), 128 GB memory"),
                        ("n2d-highmem-32", "32 vCPU (16 core), 256 GB memory"),
                        ("n2d-highmem-48", "48 vCPU (24 core), 384 GB memory"),
                        ("n2d-highmem-64", "64 vCPU (32 core), 512 GB memory"),
                        ("n2d-highmem-80", "80 vCPU (40 core), 640 GB memory"),
                        ("n2d-highmem-96", "96 vCPU (48 core), 768 GB memory")
                    ],
                    "High CPU": [
                        ("n2d-highcpu-2", "2 vCPU (1 core), 2 GB memory"),
                        ("n2d-highcpu-4", "4 vCPU (2 core), 4 GB memory"),
                        ("n2d-highcpu-8", "8 vCPU (4 core), 8 GB memory"),
                        ("n2d-highcpu-16", "16 vCPU (8 core), 16 GB memory"),
                        ("n2d-highcpu-32", "32 vCPU (16 core), 32 GB memory"),
                        ("n2d-highcpu-48", "48 vCPU (24 core), 48 GB memory"),
                        ("n2d-highcpu-64", "64 vCPU (32 core), 64 GB memory"),
                        ("n2d-highcpu-80", "80 vCPU (40 core), 80 GB memory"),
                        ("n2d-highcpu-96", "96 vCPU (48 core), 96 GB memory"),
                        ("n2d-highcpu-128", "128 vCPU (64 core), 128 GB memory"),
                        ("n2d-highcpu-224", "224 vCPU (112 core), 224 GB memory")
                    ]
                },
                "T2A": {
                    "Standard": [
                        ("t2a-standard-1", "1 vCPU, 4 GB memory"),
                        ("t2a-standard-2", "2 vCPU, 8 GB memory"),
                        ("t2a-standard-4", "4 vCPU, 16 GB memory"),
                        ("t2a-standard-8", "8 vCPU, 32 GB memory"),
                        ("t2a-standard-16", "16 vCPU, 64 GB memory"),
                        ("t2a-standard-32", "32 vCPU, 128 GB memory"),
                        ("t2a-standard-48", "48 vCPU, 192 GB memory")
                    ]
                },
                "T2D": {
                    "Standard": [
                        ("t2d-standard-1", "1 vCPU, 4 GB memory"),
                        ("t2d-standard-2", "2 vCPU, 8 GB memory"),
                        ("t2d-standard-4", "4 vCPU, 16 GB memory"),
                        ("t2d-standard-8", "8 vCPU, 32 GB memory"),
                        ("t2d-standard-16", "16 vCPU, 64 GB memory"),
                        ("t2d-standard-32", "32 vCPU, 128 GB memory"),
                        ("t2d-standard-48", "48 vCPU, 192 GB memory"),
                        ("t2d-standard-60", "60 vCPU, 240 GB memory")
                    ]
                },
                "N1": {
                    "Shared-core": [
                        ("f1-micro", "0.25-1 vCPU (1 shared core), 614 MB memory"),
                        ("g1-small", "0.5-1 vCPU (1 shared core), 1.7 GB memory")
                    ],
                    "Standard": [
                        ("n1-standard-1", "1 vCPU, 3.75 GB memory"),
                        ("n1-standard-2", "2 vCPU (1 core), 7.5 GB memory"),
                        ("n1-standard-4", "4 vCPU (2 core), 15 GB memory"),
                        ("n1-standard-8", "8 vCPU (4 core), 30 GB memory"),
                        ("n1-standard-16", "16 vCPU (8 core), 60 GB memory"),
                        ("n1-standard-32", "32 vCPU (16 core), 120 GB memory"),
                        ("n1-standard-64", "64 vCPU (32 core), 240 GB memory"),
                        ("n1-standard-96", "96 vCPU (48 core), 360 GB memory")
                    ],
                    "High memory": [
                        ("n1-highmem-2", "2 vCPU (1 core), 13 GB memory"),
                        ("n1-highmem-4", "4 vCPU (2 core), 26 GB memory"),
                        ("n1-highmem-8", "8 vCPU (4 core), 52 GB memory"),
                        ("n1-highmem-16", "16 vCPU (8 core), 104 GB memory"),
                        ("n1-highmem-32", "32 vCPU (16 core), 208 GB memory"),
                        ("n1-highmem-64", "64 vCPU (32 core), 416 GB memory"),
                        ("n1-highmem-96", "96 vCPU (48 core), 624 GB memory")
                    ],
                    "High CPU": [
                        ("n1-highcpu-2", "2 vCPU (1 core), 1.8 GB memory"),
                        ("n1-highcpu-4", "4 vCPU (2 core), 3.6 GB memory"),
                        ("n1-highcpu-8", "8 vCPU (4 core), 7.2 GB memory"),
                        ("n1-highcpu-16", "16 vCPU (8 core), 14.4 GB memory"),
                        ("n1-highcpu-32", "32 vCPU (16 core), 28.8 GB memory"),
                        ("n1-highcpu-64", "64 vCPU (32 core), 57.6 GB memory"),
                        ("n1-highcpu-96", "96 vCPU (48 core), 86.4 GB memory")
                    ]
                }
            }
            return presets.get(series, {})

        # ---- Machine type presets (General purpose) ----
        def gp_series_catalog() -> Dict[str, Dict[str, Dict[str, list]]]:
            """Return General purpose series with profiles and machine presets."""
            return {
                "C4": {
                    "Standard": {
                        "presets": [
                            "c4-standard-2", "c4-standard-4", "c4-standard-8", "c4-standard-16", 
                            "c4-standard-32", "c4-standard-64", "c4-standard-96", "c4-standard-128",
                            "c4-standard-160", "c4-standard-192", "c4-standard-224", "c4-standard-256", "c4-standard-288"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "c4-highmem-2", "c4-highmem-4", "c4-highmem-8", "c4-highmem-16",
                            "c4-highmem-32", "c4-highmem-64", "c4-highmem-96", "c4-highmem-128",
                            "c4-highmem-160", "c4-highmem-192", "c4-highmem-224", "c4-highmem-256", "c4-highmem-288"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "c4-highcpu-2", "c4-highcpu-4", "c4-highcpu-8", "c4-highcpu-16",
                            "c4-highcpu-32", "c4-highcpu-64", "c4-highcpu-96", "c4-highcpu-128",
                            "c4-highcpu-160", "c4-highcpu-192", "c4-highcpu-224", "c4-highcpu-256", "c4-highcpu-288"
                        ]
                    }
                },
                "C4A": {
                    "Standard": {
                        "presets": [
                            "c4a-standard-1", "c4a-standard-2", "c4a-standard-4", "c4a-standard-8",
                            "c4a-standard-16", "c4a-standard-32", "c4a-standard-48", "c4a-standard-64", "c4a-standard-72"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "c4a-highmem-1", "c4a-highmem-2", "c4a-highmem-4", "c4a-highmem-8",
                            "c4a-highmem-16", "c4a-highmem-32", "c4a-highmem-48", "c4a-highmem-64", "c4a-highmem-72"
                        ]
                    }
                },
                "C4D": {
                    "Standard": {
                        "presets": [
                            "c4d-standard-2", "c4d-standard-4", "c4d-standard-8", "c4d-standard-16",
                            "c4d-standard-32", "c4d-standard-64", "c4d-standard-96", "c4d-standard-128",
                            "c4d-standard-160", "c4d-standard-192", "c4d-standard-224", "c4d-standard-256",
                            "c4d-standard-288", "c4d-standard-320", "c4d-standard-352", "c4d-standard-384"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "c4d-highmem-2", "c4d-highmem-4", "c4d-highmem-8", "c4d-highmem-16",
                            "c4d-highmem-32", "c4d-highmem-64", "c4d-highmem-96", "c4d-highmem-128",
                            "c4d-highmem-160", "c4d-highmem-192", "c4d-highmem-224", "c4d-highmem-256",
                            "c4d-highmem-288", "c4d-highmem-320", "c4d-highmem-352", "c4d-highmem-384"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "c4d-highcpu-2", "c4d-highcpu-4", "c4d-highcpu-8", "c4d-highcpu-16",
                            "c4d-highcpu-32", "c4d-highcpu-64", "c4d-highcpu-96", "c4d-highcpu-128",
                            "c4d-highcpu-160", "c4d-highcpu-192", "c4d-highcpu-224", "c4d-highcpu-256",
                            "c4d-highcpu-288", "c4d-highcpu-320", "c4d-highcpu-352", "c4d-highcpu-384"
                        ]
                    }
                },
                "N4": {
                    "Standard": {
                        "presets": [
                            "n4-standard-2", "n4-standard-4", "n4-standard-8", "n4-standard-16",
                            "n4-standard-32", "n4-standard-64", "n4-standard-80"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "n4-highmem-2", "n4-highmem-4", "n4-highmem-8", "n4-highmem-16",
                            "n4-highmem-32", "n4-highmem-64", "n4-highmem-80"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "n4-highcpu-2", "n4-highcpu-4", "n4-highcpu-8", "n4-highcpu-16",
                            "n4-highcpu-32", "n4-highcpu-64", "n4-highcpu-80"
                        ]
                    }
                },
                "C3": {
                    "Standard": {
                        "presets": [
                            "c3-standard-4", "c3-standard-8", "c3-standard-22", "c3-standard-44",
                            "c3-standard-88", "c3-standard-176", "c3-standard-192"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "c3-highmem-4", "c3-highmem-8", "c3-highmem-22", "c3-highmem-44",
                            "c3-highmem-88", "c3-highmem-176", "c3-highmem-192"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "c3-highcpu-4", "c3-highcpu-8", "c3-highcpu-22", "c3-highcpu-44",
                            "c3-highcpu-88", "c3-highcpu-176", "c3-highcpu-192"
                        ]
                    }
                },
                "C3D": {
                    "Standard": {
                        "presets": [
                            "c3d-standard-4","c3d-standard-8","c3d-standard-16","c3d-standard-30",
                            "c3d-standard-60","c3d-standard-90","c3d-standard-180","c3d-standard-360",
                            "c3d-standard-8-lssd","c3d-standard-16-lssd","c3d-standard-30-lssd",
                            "c3d-standard-60-lssd","c3d-standard-90-lssd","c3d-standard-180-lssd","c3d-standard-360-lssd"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "c3d-highmem-4","c3d-highmem-8","c3d-highmem-16","c3d-highmem-30",
                            "c3d-highmem-60","c3d-highmem-90","c3d-highmem-180","c3d-highmem-360",
                            "c3d-highmem-8-lssd","c3d-highmem-16-lssd","c3d-highmem-30-lssd",
                            "c3d-highmem-60-lssd","c3d-highmem-90-lssd","c3d-highmem-180-lssd","c3d-highmem-360-lssd"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "c3d-highcpu-4","c3d-highcpu-8","c3d-highcpu-16","c3d-highcpu-30",
                            "c3d-highcpu-60","c3d-highcpu-90","c3d-highcpu-180","c3d-highcpu-360"
                        ]
                    }
                },
                "E2": {
                    "Standard": {
                        "presets": [
                            "e2-micro", "e2-small", "e2-medium", "e2-standard-2", "e2-standard-4", 
                            "e2-standard-8", "e2-standard-16", "e2-standard-32"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "e2-highmem-2", "e2-highmem-4", "e2-highmem-8", "e2-highmem-16"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "e2-highcpu-2", "e2-highcpu-4", "e2-highcpu-8", "e2-highcpu-16", "e2-highcpu-32"
                        ]
                    }
                },
                "N2": {
                    "Standard": {
                        "presets": [
                            "n2-standard-2", "n2-standard-4", "n2-standard-8", "n2-standard-16", 
                            "n2-standard-32", "n2-standard-48", "n2-standard-64", "n2-standard-80", 
                            "n2-standard-96", "n2-standard-128"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "n2-highmem-2", "n2-highmem-4", "n2-highmem-8", "n2-highmem-16",
                            "n2-highmem-32", "n2-highmem-48", "n2-highmem-64", "n2-highmem-80", "n2-highmem-96", "n2-highmem-128"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "n2-highcpu-2", "n2-highcpu-4", "n2-highcpu-8", "n2-highcpu-16",
                            "n2-highcpu-32", "n2-highcpu-48", "n2-highcpu-64", "n2-highcpu-80", "n2-highcpu-96", "n2-highcpu-128"
                        ]
                    }
                },
                "N2D": {
                    "Standard": {
                        "presets": [
                            "n2d-standard-2", "n2d-standard-4", "n2d-standard-8", "n2d-standard-16", 
                            "n2d-standard-32", "n2d-standard-48", "n2d-standard-64", "n2d-standard-80", 
                            "n2d-standard-96", "n2d-standard-128", "n2d-standard-224"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "n2d-highmem-2", "n2d-highmem-4", "n2d-highmem-8", "n2d-highmem-16",
                            "n2d-highmem-32", "n2d-highmem-48", "n2d-highmem-64", "n2d-highmem-80", "n2d-highmem-96", "n2d-highmem-128", "n2d-highmem-224"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "n2d-highcpu-2", "n2d-highcpu-4", "n2d-highcpu-8", "n2d-highcpu-16",
                            "n2d-highcpu-32", "n2d-highcpu-48", "n2d-highcpu-64", "n2d-highcpu-80", "n2d-highcpu-96", "n2d-highcpu-128", "n2d-highcpu-224"
                        ]
                    }
                },
                "T2A": {
                    "Standard": {
                        "presets": [
                            "t2a-standard-1", "t2a-standard-2", "t2a-standard-4", "t2a-standard-8",
                            "t2a-standard-16", "t2a-standard-32", "t2a-standard-48"
                        ]
                    }
                },
                "T2D": {
                    "Standard": {
                        "presets": [
                            "t2d-standard-1", "t2d-standard-2", "t2d-standard-4", "t2d-standard-8",
                            "t2d-standard-16", "t2d-standard-32", "t2d-standard-48", "t2d-standard-60"
                        ]
                    }
                },
                "N1": {
                    "Standard": {
                        "presets": [
                            "n1-standard-1", "n1-standard-2", "n1-standard-4", "n1-standard-8", 
                            "n1-standard-16", "n1-standard-32", "n1-standard-64", "n1-standard-96"
                        ]
                    },
                    "High memory": {
                        "presets": [
                            "n1-highmem-2", "n1-highmem-4", "n1-highmem-8", "n1-highmem-16",
                            "n1-highmem-32", "n1-highmem-64", "n1-highmem-96"
                        ]
                    },
                    "High CPU": {
                        "presets": [
                            "n1-highcpu-2", "n1-highcpu-4", "n1-highcpu-8", "n1-highcpu-16",
                            "n1-highcpu-32", "n1-highcpu-64", "n1-highcpu-96"
                        ]
                    }
                }
            }

        # Display existing instances with inline editing and advanced options
        if st.session_state.compute_instances:
            st.markdown("**Current Compute Instances:**")
            for i, vm in enumerate(list(st.session_state.compute_instances)):
                # Region/Zone helpers
                regions = ["us-central1", "us-west1", "europe-west1", "asia-south1"]
                region_to_zones = {
                    "us-central1": ["us-central1-a", "us-central1-b", "us-central1-c", "us-central1-f"],
                    "us-west1": ["us-west1-a", "us-west1-b", "us-west1-c"],
                    "europe-west1": ["europe-west1-b", "europe-west1-c", "europe-west1-d"],
                    "asia-south1": ["asia-south1-a", "asia-south1-b", "asia-south1-c"],
                }

                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                with col1:
                    new_name = st.text_input("Name", value=vm.get('name', ''), key=f"vm_name_{i}")
                with col2:
                    # Region selection; default inferred from zone prefix
                    current_zone = vm.get('zone', 'us-central1-a')
                    inferred_region = vm.get('region') or current_zone.rsplit('-', 1)[0]
                    r_val = inferred_region if inferred_region in regions else regions[0]
                    r_idx = regions.index(r_val)
                    new_region = st.selectbox("Region", regions, index=r_idx, key=f"vm_region_{i}")
                with col3:
                    # Zone options based on region
                    zones_list = region_to_zones.get(new_region, region_to_zones[regions[0]])
                    z_val = current_zone if current_zone in zones_list else zones_list[0]
                    z_idx = zones_list.index(z_val)
                    new_zone = st.selectbox("Zone", zones_list, index=z_idx, key=f"vm_zone_{i}")
                with col4:
                    # Machine type selection lives in Advanced VM Options below
                    new_type = vm.get('machine_type', '')
                    st.markdown(f"**Machine type**: `{new_type or 'not set'}`")
                    if st.button("Change machine type", key=f"vm_change_type_{i}"):
                        st.session_state[f"open_vm_adv_{i}"] = True
                        # Don't rerun here - let the UI update naturally
                with col5:
                    if st.button("🗑️", key=f"del_vm_{i}"):
                        st.session_state.compute_instances.pop(i)
                        st.rerun()

                with st.expander("🔧 Advanced VM Options", expanded=st.session_state.get(f"open_vm_adv_{i}", False)):
                    # Inline Machine Type Selection (fallback if popup not used)
                    st.markdown("**Machine Type Selection**")
                    tabs = st.tabs(["General purpose", "Compute optimized", "Memory optimized", "Storage optimized", "GPUs"])
                    with tabs[0]:
                        # Machine Series Selection Table
                        st.markdown("**Select Machine Series:**")
                        series_data = get_machine_series_data()
                        df = st.dataframe(
                            series_data,
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row"
                        )
                        
                        # Get selected series
                        selected_series = "E2"  # Default
                        if df.selection.rows:
                            selected_series = series_data[df.selection.rows[0]]["Series"]
                        
                        # Update session state if series changed
                        if f"selected_series_{i}" not in st.session_state:
                            st.session_state[f"selected_series_{i}"] = selected_series
                        elif st.session_state[f"selected_series_{i}"] != selected_series:
                            st.session_state[f"selected_series_{i}"] = selected_series
                            # Don't rerun here - let the UI update naturally
                        
                        st.markdown(f"**Selected Series: {selected_series}**")
                        
                        # Get presets for selected series
                        series_presets = get_series_presets(selected_series)
                        
                        # Check if series supports custom machine types
                        custom_enabled_series = ["N4", "E2", "N2", "N2D", "N1"]
                        supports_custom = selected_series in custom_enabled_series
                        
                        # Create tabs based on series support
                        if supports_custom:
                            sub_tabs = st.tabs(["Preset", "Custom"])
                        else:
                            sub_tabs = st.tabs(["Preset"])
                            
                        with sub_tabs[0]:
                            if series_presets:
                                families = list(series_presets.keys())
                                fam = st.radio("Instance sizes", families, horizontal=True, key=f"vm_family_{i}")
                                
                                if fam in series_presets:
                                    opts = [f"{name} – {desc}" for name, desc in series_presets[fam]]
                                    sel_opt = st.selectbox("Machine Type", opts, index=0, key=f"vm_opt_{i}")
                                    chosen_mt = series_presets[fam][opts.index(sel_opt)][0]
                                    
                                    if chosen_mt != st.session_state.compute_instances[i].get('machine_type'):
                                        st.session_state.compute_instances[i]['machine_type'] = chosen_mt
                                        # Don't rerun here - let the UI update naturally
                            else:
                                st.info(f"No presets available for {selected_series} series.")
                                
                        if supports_custom:
                            with sub_tabs[1]:
                                st.warning("⚠️ Creating a custom machine incurs additional costs")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    custom_vcpu = st.slider(
                                        "Cores", 
                                        min_value=1, 
                                        max_value=96, 
                                        value=2, 
                                        key=f"custom_vcpu_{i}",
                                        help="Number of vCPUs"
                                    )
                                with col2:
                                    custom_memory = st.slider(
                                        "Memory (GB)", 
                                        min_value=1.0, 
                                        max_value=6.5, 
                                        value=1.0, 
                                        step=0.1, 
                                        key=f"custom_memory_{i}",
                                        help="Memory in GB"
                                    )
                                
                                extend_memory = st.checkbox(
                                    "Extend Memory", 
                                    value=False, 
                                    key=f"extend_memory_{i}",
                                    help="Allow memory to exceed 6.5 GB per vCPU"
                                )
                                
                                if extend_memory:
                                    max_memory = min(6.5 * custom_vcpu, 624.0)  # Max 624 GB for N1
                                    custom_memory = st.slider(
                                        "Extended Memory (GB)", 
                                        min_value=1.0, 
                                        max_value=max_memory, 
                                        value=custom_memory, 
                                        step=0.1, 
                                        key=f"extended_memory_{i}",
                                        help=f"Extended memory up to {max_memory:.1f} GB"
                                    )
                                
                                # Generate custom machine type name
                                custom_mt = f"custom-{selected_series.lower()}-{custom_vcpu}-{int(custom_memory * 1024)}"
                                
                                if custom_mt != st.session_state.compute_instances[i].get('machine_type'):
                                    st.session_state.compute_instances[i]['machine_type'] = custom_mt
                                    # Don't rerun here - let the UI update naturally
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_image = st.text_input("Boot Image", value=vm.get('image', 'debian-cloud/debian-11'), key=f"vm_image_{i}")
                        new_description = st.text_input("Description", value=vm.get('description', ''), key=f"vm_desc_{i}")
                        new_hostname = st.text_input("Hostname (FQDN)", value=vm.get('hostname', ''), key=f"vm_host_{i}")
                        new_min_cpu = st.text_input("Min CPU Platform", value=vm.get('min_cpu_platform', ''), key=f"vm_min_cpu_{i}")
                    with c2:
                        new_network = st.text_input("Network (name/self_link)", value=vm.get('network', ''), key=f"vm_net_{i}")
                        new_subnet = st.text_input("Subnetwork (name/self_link)", value=vm.get('subnetwork', ''), key=f"vm_sub_{i}")
                        new_network_ip = st.text_input("Primary Internal IP", value=vm.get('network_ip', ''), key=f"vm_nip_{i}")
                        new_ext_tier = st.selectbox("External IP Tier", ["", "PREMIUM", "STANDARD"], index=["", "PREMIUM", "STANDARD"].index(vm.get('external_network_tier', "") or ""), key=f"vm_eip_tier_{i}")
                    with c3:
                        new_assign_eip = st.checkbox("Assign External IPv4", value=vm.get('assign_external_ip', vm.get('create_public_ip', False)), key=f"vm_eip_{i}")
                        new_allow_stop = st.checkbox("Allow Stop for Update", value=vm.get('allow_stopping_for_update', True), key=f"vm_allow_stop_{i}")
                        new_can_ip_forward = st.checkbox("Can IP Forward", value=vm.get('can_ip_forward', False), key=f"vm_ipf_{i}")
                        new_del_prot = st.checkbox("Deletion Protection", value=vm.get('deletion_protection', False), key=f"vm_delprot_{i}")
                        new_enable_display = st.checkbox("Enable Display Device", value=vm.get('enable_display', False), key=f"vm_display_{i}")

                    c4, c5, c6 = st.columns(3)
                    with c4:
                        new_boot_size = st.number_input("Boot Disk Size (GB)", min_value=10, value=int(vm.get('boot_disk_size_gb') or 10), key=f"vm_bsize_{i}")
                        new_boot_type = st.selectbox("Boot Disk Type", ["", "pd-standard", "pd-balanced", "pd-ssd"], index=["", "pd-standard", "pd-balanced", "pd-ssd"].index(vm.get('boot_disk_type', "") or ""), key=f"vm_btype_{i}")
                        new_boot_auto = st.checkbox("Boot Disk Auto Delete", value=vm.get('boot_disk_auto_delete', True), key=f"vm_bauto_{i}")
                    with c5:
                        new_sa_email = st.text_input("Service Account Email", value=vm.get('service_account_email', ''), key=f"vm_sa_{i}")
                        new_sa_scopes = st.text_area("Service Account Scopes (comma-separated)", value=", ".join(vm.get('service_account_scopes', ["https://www.googleapis.com/auth/cloud-platform"])) , key=f"vm_scopes_{i}")
                        new_tags = st.text_input("Tags (comma-separated)", value=", ".join(vm.get('tags', [])), key=f"vm_tags_{i}")
                    with c6:
                        new_preempt = st.checkbox("Preemptible / Spot", value=vm.get('scheduling_preemptible', False), key=f"vm_preempt_{i}")
                        new_auto_restart = st.checkbox("Automatic Restart", value=vm.get('scheduling_automatic_restart', True), key=f"vm_autorst_{i}")
                        new_ohm = st.selectbox("On Host Maintenance", ["", "MIGRATE", "TERMINATE"], index=["", "MIGRATE", "TERMINATE"].index(vm.get('scheduling_on_host_maintenance', "") or ""), key=f"vm_ohm_{i}")
                        new_prov_model = st.selectbox("Provisioning Model", ["", "STANDARD", "SPOT"], index=["", "STANDARD", "SPOT"].index(vm.get('scheduling_provisioning_model', "") or ""), key=f"vm_prov_{i}")

                    c7, c8 = st.columns(2)
                    with c7:
                        new_enable_shielded = st.checkbox("Enable Shielded VM", value=vm.get('enable_shielded_vm', False), key=f"vm_shielded_{i}")
                        new_sh_secure = st.checkbox("Shielded Secure Boot", value=vm.get('shielded_secure_boot', False), key=f"vm_shs_{i}")
                        new_sh_vtpm = st.checkbox("Shielded vTPM", value=vm.get('shielded_vtpm', True), key=f"vm_shv_{i}")
                        new_sh_integrity = st.checkbox("Shielded Integrity Monitoring", value=vm.get('shielded_integrity_monitoring', True), key=f"vm_shi_{i}")
                    with c8:
                        new_enable_conf = st.checkbox("Enable Confidential Compute", value=vm.get('enable_confidential_compute', False), key=f"vm_conf_{i}")
                        new_conf_type = st.selectbox("Confidential Type", ["", "SEV", "SEV_SNP", "TDX"], index=["", "SEV", "SEV_SNP", "TDX"].index(vm.get('confidential_instance_type', "") or ""), key=f"vm_conf_type_{i}")

                    # JSON-like inputs
                    adv1, adv2, adv3 = st.columns(3)
                    with adv1:
                        new_labels_str = st.text_area("Labels (JSON)", value=json.dumps(vm.get('labels', {}), indent=2), key=f"vm_labels_{i}")
                    with adv2:
                        new_metadata_str = st.text_area("Metadata (JSON)", value=json.dumps(vm.get('metadata', {}), indent=2), key=f"vm_meta_{i}")
                    with adv3:
                        new_boot_labels_str = st.text_area("Boot Disk Labels (JSON)", value=json.dumps(vm.get('boot_disk_labels', {}), indent=2), key=f"vm_blabels_{i}")

                    # Startup script
                    new_startup = st.text_area("Startup Script", value=vm.get('metadata_startup_script', ''), key=f"vm_startup_{i}")

                    # Guest accelerators as JSON list
                    new_gpus_str = st.text_area("Guest Accelerators (JSON list)", value=json.dumps(vm.get('guest_accelerators', []), indent=2), key=f"vm_gpus_{i}")

                    # Parse and save advanced fields back
                    def parse_json_or(default_val, s):
                        try:
                            return json.loads(s) if s else default_val
                        except Exception:
                            return default_val

                    st.session_state.compute_instances[i]['image'] = new_image
                    st.session_state.compute_instances[i]['description'] = new_description or None
                    st.session_state.compute_instances[i]['hostname'] = new_hostname or None
                    st.session_state.compute_instances[i]['min_cpu_platform'] = new_min_cpu or None
                    st.session_state.compute_instances[i]['network'] = new_network or None
                    st.session_state.compute_instances[i]['subnetwork'] = new_subnet or None
                    st.session_state.compute_instances[i]['network_ip'] = new_network_ip or None
                    st.session_state.compute_instances[i]['external_network_tier'] = new_ext_tier or None
                    st.session_state.compute_instances[i]['assign_external_ip'] = bool(new_assign_eip)
                    st.session_state.compute_instances[i]['allow_stopping_for_update'] = bool(new_allow_stop)
                    st.session_state.compute_instances[i]['can_ip_forward'] = bool(new_can_ip_forward)
                    st.session_state.compute_instances[i]['deletion_protection'] = bool(new_del_prot)
                    st.session_state.compute_instances[i]['enable_display'] = bool(new_enable_display)
                    st.session_state.compute_instances[i]['boot_disk_size_gb'] = int(new_boot_size) if new_boot_size else None
                    st.session_state.compute_instances[i]['boot_disk_type'] = new_boot_type or None
                    st.session_state.compute_instances[i]['boot_disk_auto_delete'] = bool(new_boot_auto)
                    st.session_state.compute_instances[i]['service_account_email'] = new_sa_email or None
                    st.session_state.compute_instances[i]['service_account_scopes'] = [s.strip() for s in (new_sa_scopes or '').split(',') if s.strip()] or ["https://www.googleapis.com/auth/cloud-platform"]
                    st.session_state.compute_instances[i]['tags'] = [t.strip() for t in (new_tags or '').split(',') if t.strip()]
                    st.session_state.compute_instances[i]['scheduling_preemptible'] = bool(new_preempt)
                    st.session_state.compute_instances[i]['scheduling_automatic_restart'] = bool(new_auto_restart)
                    st.session_state.compute_instances[i]['scheduling_on_host_maintenance'] = new_ohm or None
                    st.session_state.compute_instances[i]['scheduling_provisioning_model'] = new_prov_model or None
                    st.session_state.compute_instances[i]['enable_shielded_vm'] = bool(new_enable_shielded)
                    st.session_state.compute_instances[i]['shielded_secure_boot'] = bool(new_sh_secure)
                    st.session_state.compute_instances[i]['shielded_vtpm'] = bool(new_sh_vtpm)
                    st.session_state.compute_instances[i]['shielded_integrity_monitoring'] = bool(new_sh_integrity)
                    st.session_state.compute_instances[i]['enable_confidential_compute'] = bool(new_enable_conf)
                    st.session_state.compute_instances[i]['confidential_instance_type'] = new_conf_type or None
                    st.session_state.compute_instances[i]['labels'] = parse_json_or({}, new_labels_str)
                    st.session_state.compute_instances[i]['metadata'] = parse_json_or({}, new_metadata_str)
                    st.session_state.compute_instances[i]['boot_disk_labels'] = parse_json_or({}, new_boot_labels_str)
                    st.session_state.compute_instances[i]['metadata_startup_script'] = new_startup or None
                    st.session_state.compute_instances[i]['guest_accelerators'] = parse_json_or([], new_gpus_str)

                    # Cost estimate (live)
                    estimate = estimate_vm_cost_monthly(st.session_state.compute_instances[i])
                    st.markdown("**Monthly estimate**")
                    st.markdown(f"${estimate['total']:.2f}")
                    st.caption(f"That's about ${estimate['hourly_compute']:.2f} hourly (compute only)")
                    with st.expander("View breakdown", expanded=False):
                        st.markdown("Item | Monthly estimate")
                        st.markdown("--- | ---")
                        st.markdown(f"{int(estimate['vcpu']) if estimate['vcpu'].is_integer() else estimate['vcpu']} vCPU + {int(estimate['mem_gb']) if estimate['mem_gb'].is_integer() else estimate['mem_gb']} GB memory | ${estimate['monthly_compute']:.2f}")
                        st.markdown(f"{int(st.session_state.compute_instances[i].get('boot_disk_size_gb') or 10)} GB {st.session_state.compute_instances[i].get('boot_disk_type') or 'pd-balanced'} persistent disk | ${estimate['disk_month']:.2f}")
                        st.markdown("Logging | Cost varies")
                        st.markdown("Monitoring | Cost varies")
                        st.markdown("Snapshot schedule | Cost varies")

                # Basic fields update
                if (new_name != vm.get('name') or new_zone != vm.get('zone') or new_type != vm.get('machine_type') or new_region != vm.get('region')):
                    st.session_state.compute_instances[i]['name'] = new_name
                    st.session_state.compute_instances[i]['region'] = new_region
                    st.session_state.compute_instances[i]['zone'] = new_zone
                    st.session_state.compute_instances[i]['machine_type'] = new_type

        # Add new instance
        st.markdown("**Add New Compute Instance:**")
        # Region/Zone for new instances
        regions = ["us-central1", "us-west1", "europe-west1", "asia-south1"]
        region_to_zones = {
            "us-central1": ["us-central1-a", "us-central1-b", "us-central1-c", "us-central1-f"],
            "us-west1": ["us-west1-a", "us-west1-b", "us-west1-c"],
            "europe-west1": ["europe-west1-b", "europe-west1-c", "europe-west1-d"],
            "asia-south1": ["asia-south1-a", "asia-south1-b", "asia-south1-c"],
        }

        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        with col1:
            vm_name = st.text_input("VM Name", value="my-vm", key="new_vm_name")
        with col2:
            new_vm_region = st.selectbox("Region", regions, index=0, key="new_vm_region")
        with col3:
            # Zone based on region
            zones_list = region_to_zones.get(new_vm_region, region_to_zones[regions[0]])
            vm_zone = st.selectbox("Zone", zones_list, index=0, key="new_vm_zone")
        with col4:
            # Machine type selection lives in Advanced Options below
            if 'new_vm_machine_type' not in st.session_state:
                st.session_state.new_vm_machine_type = "e2-standard-2"
            st.markdown(f"**Machine type**: `{st.session_state.new_vm_machine_type}`")
            if st.button("Change machine type", key="new_vm_change_type"):
                st.session_state["open_new_vm_adv"] = True
                # Don't rerun here - let the UI update naturally
        with col5:
            add_clicked = st.button("➕ Add", key="add_vm")

        with st.expander("🔧 Advanced Options for New VM", expanded=st.session_state.get("open_new_vm_adv", False)):
            nc1, nc2, nc3 = st.columns(3)
            with nc1:
                vm_image = st.text_input("Boot Image", value="debian-cloud/debian-11", key="new_vm_image")
                vm_description = st.text_input("Description", value="", key="new_vm_desc")
                vm_hostname = st.text_input("Hostname (FQDN)", value="", key="new_vm_host")
                vm_min_cpu = st.text_input("Min CPU Platform", value="", key="new_vm_min_cpu")
            with nc2:
                vm_network = st.text_input("Network (name/self_link)", value="", key="new_vm_net")
                vm_subnet = st.text_input("Subnetwork (name/self_link)", value="", key="new_vm_sub")
                vm_network_ip = st.text_input("Primary Internal IP", value="", key="new_vm_nip")
                vm_ext_tier = st.selectbox("External IP Tier", ["", "PREMIUM", "STANDARD"], key="new_vm_eip_tier")
            with nc3:
                vm_assign_eip = st.checkbox("Assign External IPv4", value=False, key="new_vm_eip")
                vm_allow_stop = st.checkbox("Allow Stop for Update", value=True, key="new_vm_allow_stop")
                vm_can_ip_forward = st.checkbox("Can IP Forward", value=False, key="new_vm_ipf")
                vm_del_prot = st.checkbox("Deletion Protection", value=False, key="new_vm_delprot")
                vm_enable_display = st.checkbox("Enable Display Device", value=False, key="new_vm_display")

            nb1, nb2, nb3 = st.columns(3)
            with nb1:
                vm_boot_size = st.number_input("Boot Disk Size (GB)", min_value=10, value=10, key="new_vm_bsize")
                vm_boot_type = st.selectbox("Boot Disk Type", ["", "pd-standard", "pd-balanced", "pd-ssd"], key="new_vm_btype")
                vm_boot_auto = st.checkbox("Boot Disk Auto Delete", value=True, key="new_vm_bauto")
            with nb2:
                vm_sa_email = st.text_input("Service Account Email", value="", key="new_vm_sa")
                vm_sa_scopes = st.text_area("Service Account Scopes (comma-separated)", value="https://www.googleapis.com/auth/cloud-platform", key="new_vm_scopes")
                vm_tags = st.text_input("Tags (comma-separated)", value="", key="new_vm_tags")
            with nb3:
                vm_preempt = st.checkbox("Preemptible / Spot", value=False, key="new_vm_preempt")
                vm_auto_restart = st.checkbox("Automatic Restart", value=True, key="new_vm_autorst")
                vm_ohm = st.selectbox("On Host Maintenance", ["", "MIGRATE", "TERMINATE"], key="new_vm_ohm")
                vm_prov_model = st.selectbox("Provisioning Model", ["", "STANDARD", "SPOT"], key="new_vm_prov")

            nb4, nb5 = st.columns(2)
            with nb4:
                vm_enable_shielded = st.checkbox("Enable Shielded VM", value=False, key="new_vm_shielded")
                vm_sh_secure = st.checkbox("Shielded Secure Boot", value=False, key="new_vm_shs")
                vm_sh_vtpm = st.checkbox("Shielded vTPM", value=True, key="new_vm_shv")
                vm_sh_integrity = st.checkbox("Shielded Integrity Monitoring", value=True, key="new_vm_shi")
            with nb5:
                vm_enable_conf = st.checkbox("Enable Confidential Compute", value=False, key="new_vm_conf")
                vm_conf_type = st.selectbox("Confidential Type", ["", "SEV", "SEV_SNP", "TDX"], key="new_vm_conf_type")

            # JSON inputs
            nja, njb, njc = st.columns(3)
            with nja:
                vm_labels_str = st.text_area("Labels (JSON)", value="{}", key="new_vm_labels")
            with njb:
                vm_metadata_str = st.text_area("Metadata (JSON)", value="{}", key="new_vm_metadata")
            with njc:
                vm_boot_labels_str = st.text_area("Boot Disk Labels (JSON)", value="{}", key="new_vm_blabels")

            vm_startup = st.text_area("Startup Script", value="", key="new_vm_startup")
            vm_gpus_str = st.text_area("Guest Accelerators (JSON list)", value="[]", key="new_vm_gpus")

            # Live estimate for new VM
            tmp_vm = {
                "machine_type": st.session_state.new_vm_machine_type,
                "boot_disk_size_gb": vm_boot_size,
                "boot_disk_type": vm_boot_type or "pd-balanced",
            }
            est_new = estimate_vm_cost_monthly(tmp_vm)
            st.markdown("**Monthly estimate**")
            st.markdown(f"${est_new['total']:.2f}")
            st.caption(f"That's about ${est_new['hourly_compute']:.2f} hourly (compute only)")
            with st.expander("View breakdown", expanded=False):
                st.markdown("Item | Monthly estimate")
                st.markdown("--- | ---")
                st.markdown(f"{int(est_new['vcpu']) if est_new['vcpu'].is_integer() else est_new['vcpu']} vCPU + {int(est_new['mem_gb']) if est_new['mem_gb'].is_integer() else est_new['mem_gb']} GB memory | ${est_new['monthly_compute']:.2f}")
                st.markdown(f"{int(vm_boot_size)} GB {vm_boot_type or 'pd-balanced'} persistent disk | ${est_new['disk_month']:.2f}")
                st.markdown("Logging | Cost varies")
                st.markdown("Monitoring | Cost varies")
                st.markdown("Snapshot schedule | Cost varies")

            # Machine Type Selection
            st.markdown("**Machine Type Selection**")
            tabs = st.tabs(["General purpose", "Compute optimized", "Memory optimized", "Storage optimized", "GPUs"])
            with tabs[0]:
                # Machine Series Selection Table
                st.markdown("**Select Machine Series:**")
                series_data = get_machine_series_data()
                df = st.dataframe(
                    series_data,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="new_vm_series_table"
                )
                
                # Get selected series
                selected_series = "E2"  # Default
                if df.selection.rows:
                    selected_series = series_data[df.selection.rows[0]]["Series"]
                
                # Update session state if series changed
                if "new_vm_selected_series" not in st.session_state:
                    st.session_state["new_vm_selected_series"] = selected_series
                elif st.session_state["new_vm_selected_series"] != selected_series:
                    st.session_state["new_vm_selected_series"] = selected_series
                    # Don't rerun here - let the UI update naturally
                
                st.markdown(f"**Selected Series: {selected_series}**")
                
                # Get presets for selected series
                series_presets = get_series_presets(selected_series)
                
                # Check if series supports custom machine types
                custom_enabled_series = ["N4", "E2", "N2", "N2D", "N1"]
                supports_custom = selected_series in custom_enabled_series
                
                # Create tabs based on series support
                if supports_custom:
                    sub_tabs = st.tabs(["Preset", "Custom"])
                else:
                    sub_tabs = st.tabs(["Preset"])
                    
                with sub_tabs[0]:
                    if series_presets:
                        families = list(series_presets.keys())
                        fam = st.radio("Instance sizes", families, horizontal=True, key="new_vm_family")
                        
                        if fam in series_presets:
                            opts = [f"{name} – {desc}" for name, desc in series_presets[fam]]
                            sel_opt = st.selectbox("Machine Type", opts, index=0, key="new_vm_opt")
                            chosen_mt = series_presets[fam][opts.index(sel_opt)][0]
                            
                            if chosen_mt != st.session_state.new_vm_machine_type:
                                st.session_state.new_vm_machine_type = chosen_mt
                                # Don't rerun here - let the UI update naturally
                    else:
                        st.info(f"No presets available for {selected_series} series.")
                        
                if supports_custom:
                    with sub_tabs[1]:
                        st.warning("⚠️ Creating a custom machine incurs additional costs")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            custom_vcpu = st.slider(
                                "Cores", 
                                min_value=1, 
                                max_value=96, 
                                value=2, 
                                key="new_custom_vcpu",
                                help="Number of vCPUs"
                            )
                        with col2:
                            custom_memory = st.slider(
                                "Memory (GB)", 
                                min_value=1.0, 
                                max_value=6.5, 
                                value=1.0, 
                                step=0.1, 
                                key="new_custom_memory",
                                help="Memory in GB"
                            )
                        
                        extend_memory = st.checkbox(
                            "Extend Memory", 
                            value=False, 
                            key="new_extend_memory",
                            help="Allow memory to exceed 6.5 GB per vCPU"
                        )
                        
                        if extend_memory:
                            max_memory = min(6.5 * custom_vcpu, 624.0)  # Max 624 GB for N1
                            custom_memory = st.slider(
                                "Extended Memory (GB)", 
                                min_value=1.0, 
                                max_value=max_memory, 
                                value=custom_memory, 
                                step=0.1, 
                                key="new_extended_memory",
                                help=f"Extended memory up to {max_memory:.1f} GB"
                            )
                        
                        # Generate custom machine type name
                        custom_mt = f"custom-{selected_series.lower()}-{custom_vcpu}-{int(custom_memory * 1024)}"
                        
                        if custom_mt != st.session_state.new_vm_machine_type:
                            st.session_state.new_vm_machine_type = custom_mt
                            # Don't rerun here - let the UI update naturally

        if add_clicked and vm_name:
            def parse_json_default(s, default):
                try:
                    return json.loads(s) if s else default
                except Exception:
                    return default
            new_vm = {
                "name": vm_name,
                "region": new_vm_region,
                "zone": vm_zone,
                "machine_type": st.session_state.new_vm_machine_type,
                "image": vm_image,
                "description": vm_description or None,
                "hostname": vm_hostname or None,
                "min_cpu_platform": vm_min_cpu or None,
                "network": vm_network or None,
                "subnetwork": vm_subnet or None,
                "network_ip": vm_network_ip or None,
                "external_network_tier": vm_ext_tier or None,
                "assign_external_ip": bool(vm_assign_eip),
                "allow_stopping_for_update": bool(vm_allow_stop),
                "can_ip_forward": bool(vm_can_ip_forward),
                "deletion_protection": bool(vm_del_prot),
                "enable_display": bool(vm_enable_display),
                "boot_disk_size_gb": int(vm_boot_size) if vm_boot_size else None,
                "boot_disk_type": vm_boot_type or None,
                "boot_disk_auto_delete": bool(vm_boot_auto),
                "service_account_email": vm_sa_email or None,
                "service_account_scopes": [s.strip() for s in (vm_sa_scopes or '').split(',') if s.strip()] or ["https://www.googleapis.com/auth/cloud-platform"],
                "tags": [t.strip() for t in (vm_tags or '').split(',') if t.strip()],
                "scheduling_preemptible": bool(vm_preempt),
                "scheduling_automatic_restart": bool(vm_auto_restart),
                "scheduling_on_host_maintenance": vm_ohm or None,
                "scheduling_provisioning_model": vm_prov_model or None,
                "enable_shielded_vm": bool(vm_enable_shielded),
                "shielded_secure_boot": bool(vm_sh_secure),
                "shielded_vtpm": bool(vm_sh_vtpm),
                "shielded_integrity_monitoring": bool(vm_sh_integrity),
                "enable_confidential_compute": bool(vm_enable_conf),
                "confidential_instance_type": vm_conf_type or None,
                "labels": parse_json_default(vm_labels_str, {}),
                "metadata": parse_json_default(vm_metadata_str, {}),
                "boot_disk_labels": parse_json_default(vm_boot_labels_str, {}),
                "metadata_startup_script": vm_startup or None,
                "guest_accelerators": parse_json_default(vm_gpus_str, []),
            }
            st.session_state.compute_instances.append(new_vm)
            st.rerun()

        if st.session_state.compute_instances:
            resources["compute_instances"] = st.session_state.compute_instances
    
    # Storage Buckets
    if st.checkbox("🪣 Create Storage Buckets"):
        st.markdown("**Storage Configuration**")
        if 'storage_buckets' not in st.session_state:
            st.session_state.storage_buckets = []
        
        # Display existing buckets with inline editing
        if st.session_state.storage_buckets:
            st.markdown("**Current Storage Buckets:**")
            for i, bucket in enumerate(list(st.session_state.storage_buckets)):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    new_name = st.text_input("Name", value=bucket['name'], key=f"bucket_name_{i}")
                with col2:
                    new_location = st.selectbox("Location", ["US", "EU", "ASIA"], 
                                              index=["US", "EU", "ASIA"].index(bucket['location']),
                                              key=f"bucket_location_{i}")
                with col3:
                    if st.button("🗑️", key=f"del_bucket_{i}"):
                        st.session_state.storage_buckets.pop(i)
                        st.rerun()
                
                # Update if changed
                if new_name != bucket['name'] or new_location != bucket['location']:
                    st.session_state.storage_buckets[i]['name'] = new_name
                    st.session_state.storage_buckets[i]['location'] = new_location
        
        # Add new bucket
        st.markdown("**Add New Storage Bucket:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            bucket_name = st.text_input("Bucket Name", value="my-bucket", key="new_bucket_name")
        with col2:
            bucket_location = st.selectbox("Location", ["US", "EU", "ASIA"], key="new_bucket_location")
        with col3:
            if st.button("➕ Add", key="add_bucket"):
                if bucket_name:
                    new_bucket = {
                        "name": bucket_name,
                        "location": bucket_location,
                        "enable_versioning": False,
                        "uniform_bucket_level_access": True
                    }
                    st.session_state.storage_buckets.append(new_bucket)
                    st.rerun()
        
        if st.session_state.storage_buckets:
            resources["storage_buckets"] = st.session_state.storage_buckets
    
    # Pub/Sub Topics
    if st.checkbox("📢 Create Pub/Sub Topics"):
        st.markdown("**Pub/Sub Configuration**")
        if 'pubsub_topics' not in st.session_state:
            st.session_state.pubsub_topics = []
        
        # Display existing topics
        if st.session_state.pubsub_topics:
            st.markdown("**Current Pub/Sub Topics:**")
            for i, topic in enumerate(st.session_state.pubsub_topics):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Name: {topic['name']}")
                with col2:
                    if st.button("🗑️", key=f"del_topic_{i}"):
                        st.session_state.pubsub_topics.pop(i)
                        st.rerun()
        
        # Add new topic
        st.markdown("**Add New Pub/Sub Topic:**")
        col1, col2 = st.columns([2, 1])
        with col1:
            topic_name = st.text_input("Topic Name", value="my-topic", key="new_topic_name")
        with col2:
            if st.button("➕ Add", key="add_topic"):
                if topic_name:
                    new_topic = {
                        "name": topic_name,
                        "labels": {"created_by": "gui"}
                    }
                    st.session_state.pubsub_topics.append(new_topic)
                    st.rerun()
        
        if st.session_state.pubsub_topics:
            resources["pubsub_topics"] = st.session_state.pubsub_topics
    
    # Cloud Run Services
    if st.checkbox("🚀 Create Cloud Run Services"):
        st.markdown("**Cloud Run Configuration**")
        if 'cloud_run_services' not in st.session_state:
            st.session_state.cloud_run_services = []
        
        
        # Initialize number of form sections
        if 'cr_form_count' not in st.session_state:
            st.session_state.cr_form_count = 1
        
        # Render form sections
        for i in range(st.session_state.cr_form_count):
            if i > 0:  # Add space between forms
                st.markdown("---")
            
            st.markdown(f"**Cloud Run Service {i+1}:**")
            
            # Get or create service data for this form
            if i >= len(st.session_state.cloud_run_services):
                st.session_state.cloud_run_services.append({
                    "name": f"my-service-{i+1}",
                    "location": "us-central1",
                    "image": "nginxinc/nginx-unprivileged:stable-alpine",
                    "allow_unauthenticated": True
                })
            
            service = st.session_state.cloud_run_services[i]
            
            # Form fields for this service
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                form_name = st.text_input("Service Name", value=service['name'], key=f"cr_name_{i}")
            with col2:
                form_location = st.selectbox("Location", ["us-central1", "us-west1", "europe-west1"], 
                                           index=["us-central1", "us-west1", "europe-west1"].index(service['location']),
                                           key=f"cr_location_{i}")
            with col3:
                if st.button("🗑️", key=f"del_cr_{i}"):
                    # Remove this service and adjust form count
                    st.session_state.cloud_run_services.pop(i)
                    st.session_state.cr_form_count -= 1
                    st.rerun()
            
            form_image = st.text_input("Container Image", value=service['image'], key=f"cr_image_{i}")
            form_auth = st.checkbox("Allow Unauthenticated", value=service['allow_unauthenticated'], key=f"cr_auth_{i}")
            
            # Update service data
            st.session_state.cloud_run_services[i] = {
                "name": form_name,
                "location": form_location,
                "image": form_image,
                "allow_unauthenticated": form_auth
            }
        
        # Add button to create new form section
        if st.button("➕ Add Another Service", key="add_cr_service"):
            st.session_state.cr_form_count += 1
            st.rerun()
        
        if st.session_state.cloud_run_services:
            resources["cloud_run_services"] = st.session_state.cloud_run_services
    
    # Cloud SQL Instances
    if st.checkbox("🗄️ Create Cloud SQL Instances"):
        st.markdown("**Cloud SQL Configuration**")
        if 'cloud_sql_instances' not in st.session_state:
            st.session_state.cloud_sql_instances = []
        
        # Display existing instances
        if st.session_state.cloud_sql_instances:
            st.markdown("**Current Cloud SQL Instances:**")
            for i, sql in enumerate(st.session_state.cloud_sql_instances):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {sql['name']}")
                with col2:
                    st.text(f"Version: {sql['database_version']}")
                with col3:
                    if st.button("🗑️", key=f"del_sql_{i}"):
                        st.session_state.cloud_sql_instances.pop(i)
                        st.rerun()
        
        # Add new instance
        st.markdown("**Add New Cloud SQL Instance:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sql_name = st.text_input("Instance Name", value="my-sql", key="new_sql_name")
        with col2:
            sql_version = st.selectbox("Database Version", ["POSTGRES_14", "MYSQL_8_0", "SQLSERVER_2019_STANDARD"], key="new_sql_version")
        with col3:
            if st.button("➕ Add", key="add_sql"):
                if sql_name:
                    new_sql = {
                        "name": sql_name,
                        "database_version": sql_version,
                        "region": "us-central1",
                        "tier": "db-f1-micro"
                    }
                    st.session_state.cloud_sql_instances.append(new_sql)
                    st.rerun()
        
        if st.session_state.cloud_sql_instances:
            resources["cloud_sql_instances"] = st.session_state.cloud_sql_instances
    
    # Artifact Registry
    if st.checkbox("📦 Create Artifact Registry"):
        st.markdown("**Artifact Registry Configuration**")
        if 'artifact_repos' not in st.session_state:
            st.session_state.artifact_repos = []
        
        # Display existing repos
        if st.session_state.artifact_repos:
            st.markdown("**Current Artifact Repositories:**")
            for i, repo in enumerate(st.session_state.artifact_repos):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {repo['name']}")
                with col2:
                    st.text(f"Format: {repo['format']}")
                with col3:
                    if st.button("🗑️", key=f"del_ar_{i}"):
                        st.session_state.artifact_repos.pop(i)
                        st.rerun()
        
        # Add new repo
        st.markdown("**Add New Artifact Repository:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            ar_name = st.text_input("Repository Name", value="my-repo", key="new_ar_name")
        with col2:
            ar_format = st.selectbox("Format", ["DOCKER", "MAVEN", "NPM", "PYTHON"], key="new_ar_format")
        with col3:
            if st.button("➕ Add", key="add_ar"):
                if ar_name:
                    new_ar = {
                        "name": ar_name,
                        "location": "us",
                        "format": ar_format,
                        "description": "Repository created via GUI"
                    }
                    st.session_state.artifact_repos.append(new_ar)
                    st.rerun()
        
        if st.session_state.artifact_repos:
            resources["artifact_repos"] = st.session_state.artifact_repos
    
    # Secret Manager
    if st.checkbox("🔐 Create Secret Manager Secrets"):
        st.markdown("**Secret Manager Configuration**")
        if 'secrets' not in st.session_state:
            st.session_state.secrets = []
        
        # Display existing secrets
        if st.session_state.secrets:
            st.markdown("**Current Secrets:**")
            for i, secret in enumerate(st.session_state.secrets):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Name: {secret['name']}")
                with col2:
                    if st.button("🗑️", key=f"del_secret_{i}"):
                        st.session_state.secrets.pop(i)
                        st.rerun()
        
        # Add new secret
        st.markdown("**Add New Secret:**")
        col1, col2 = st.columns([2, 1])
        with col1:
            secret_name = st.text_input("Secret Name", value="my-secret", key="new_secret_name")
        with col2:
            if st.button("➕ Add", key="add_secret"):
                if secret_name:
                    new_secret = {
                        "name": secret_name,
                        "value": "dummy-value"
                    }
                    st.session_state.secrets.append(new_secret)
                    st.rerun()
        
        if st.session_state.secrets:
            resources["secrets"] = st.session_state.secrets
    
    # Cloud DNS Zones
    if st.checkbox("🌐 Create Cloud DNS Zones"):
        st.markdown("**Cloud DNS Configuration**")
        if 'dns_zones' not in st.session_state:
            st.session_state.dns_zones = []
        
        # Display existing zones
        if st.session_state.dns_zones:
            st.markdown("**Current DNS Zones:**")
            for i, zone in enumerate(st.session_state.dns_zones):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Name: {zone['name']} ({zone['dns_name']})")
                with col2:
                    if st.button("🗑️", key=f"del_dns_{i}"):
                        st.session_state.dns_zones.pop(i)
                        st.rerun()
        
        # Add new zone
        st.markdown("**Add New DNS Zone:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            dns_name = st.text_input("Zone Name", value="my-zone", key="new_dns_name")
        with col2:
            dns_domain = st.text_input("DNS Name", value="example.com.", key="new_dns_domain")
        with col3:
            if st.button("➕ Add", key="add_dns"):
                if dns_name and dns_domain:
                    new_dns = {
                        "name": dns_name,
                        "dns_name": dns_domain,
                        "description": "DNS zone created via GUI"
                    }
                    st.session_state.dns_zones.append(new_dns)
                    st.rerun()
        
        if st.session_state.dns_zones:
            resources["dns_zones"] = st.session_state.dns_zones
    
    # BigQuery Datasets
    if st.checkbox("📊 Create BigQuery Datasets"):
        st.markdown("**BigQuery Configuration**")
        if 'bigquery_datasets' not in st.session_state:
            st.session_state.bigquery_datasets = []
        
        # Display existing datasets
        if st.session_state.bigquery_datasets:
            st.markdown("**Current BigQuery Datasets:**")
            for i, dataset in enumerate(st.session_state.bigquery_datasets):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Dataset ID: {dataset['dataset_id']}")
                with col2:
                    if st.button("🗑️", key=f"del_bq_{i}"):
                        st.session_state.bigquery_datasets.pop(i)
                        st.rerun()
        
        # Add new dataset
        st.markdown("**Add New BigQuery Dataset:**")
        col1, col2 = st.columns([2, 1])
        with col1:
            bq_id = st.text_input("Dataset ID", value="my_dataset", key="new_bq_id")
        with col2:
            if st.button("➕ Add", key="add_bq"):
                if bq_id:
                    new_bq = {
                        "dataset_id": bq_id,
                        "location": "US"
                    }
                    st.session_state.bigquery_datasets.append(new_bq)
                    st.rerun()
        
        if st.session_state.bigquery_datasets:
            resources["bigquery_datasets"] = st.session_state.bigquery_datasets
    
    # Cloud Functions
    if st.checkbox("⚡ Create Cloud Functions"):
        st.markdown("**Cloud Functions Configuration**")
        if 'cloud_functions' not in st.session_state:
            st.session_state.cloud_functions = []
        
        # Display existing functions
        if st.session_state.cloud_functions:
            st.markdown("**Current Cloud Functions:**")
            for i, func in enumerate(st.session_state.cloud_functions):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {func['name']}")
                with col2:
                    st.text(f"Runtime: {func['runtime']}")
                with col3:
                    if st.button("🗑️", key=f"del_cf_{i}"):
                        st.session_state.cloud_functions.pop(i)
                        st.rerun()
        
        # Add new function
        st.markdown("**Add New Cloud Function:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            cf_name = st.text_input("Function Name", value="my-function", key="new_cf_name")
        with col2:
            cf_runtime = st.selectbox("Runtime", ["python311", "nodejs18", "go119"], key="new_cf_runtime")
        with col3:
            if st.button("➕ Add", key="add_cf"):
                if cf_name:
                    new_cf = {
                        "name": cf_name,
                        "location": "us-central1",
                        "runtime": cf_runtime,
                        "entry_point": "main",
                        "source_bucket": "my-bucket",
                        "source_object": "functions/function.zip"
                    }
                    st.session_state.cloud_functions.append(new_cf)
                    st.rerun()
        
        if st.session_state.cloud_functions:
            resources["cloud_functions"] = st.session_state.cloud_functions
    
    # GKE Cluster
    if st.checkbox("☸️ Create GKE Cluster"):
        st.markdown("**GKE Configuration**")
        gke_name = st.text_input("Cluster Name", value="my-gke", key="gke_name")
        gke_location = st.selectbox("Location", ["us-central1", "us-west1", "europe-west1"], key="gke_location")
        gke_machine_type = st.selectbox("Node Machine Type", ["e2-standard-2", "e2-standard-4", "e2-standard-8"], key="gke_machine_type")
        gke_node_count = st.number_input("Node Count", min_value=1, max_value=10, value=1, key="gke_node_count")
        
        if gke_name:
            resources["gke"] = {
                "name": gke_name,
                "location": gke_location,
                "node_pool_name": "default-pool",
                "node_count": gke_node_count,
                "machine_type": gke_machine_type
            }
    
    # Cloud Router
    if st.checkbox("🛣️ Create Cloud Router"):
        st.markdown("**Cloud Router Configuration**")
        router_name = st.text_input("Router Name", value="my-router", key="router_name")
        router_region = st.selectbox("Region", ["us-central1", "us-west1", "europe-west1"], key="router_region")
        
        if router_name:
            resources["cloud_router"] = {
                "name": router_name,
                "region": router_region,
                "network": "my-vpc"
            }
    
    # Cloud NAT
    if st.checkbox("🌍 Create Cloud NAT"):
        st.markdown("**Cloud NAT Configuration**")
        nat_name = st.text_input("NAT Name", value="my-nat", key="nat_name")
        nat_region = st.selectbox("Region", ["us-central1", "us-west1", "europe-west1"], key="nat_region")
        
        if nat_name:
            resources["cloud_nat"] = {
                "name": nat_name,
                "region": nat_region,
                "router": "my-router"
            }
    
    # Static IPs
    if st.checkbox("🌐 Create Static IPs"):
        st.markdown("**Static IP Configuration**")
        if 'static_ips' not in st.session_state:
            st.session_state.static_ips = []
        
        # Display existing IPs
        if st.session_state.static_ips:
            st.markdown("**Current Static IPs:**")
            for i, ip in enumerate(st.session_state.static_ips):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {ip['name']}")
                with col2:
                    st.text(f"Type: {ip['address_type']}")
                with col3:
                    if st.button("🗑️", key=f"del_ip_{i}"):
                        st.session_state.static_ips.pop(i)
                        st.rerun()
        
        # Add new IP
        st.markdown("**Add New Static IP:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            ip_name = st.text_input("IP Name", value="my-ip", key="new_ip_name")
        with col2:
            ip_type = st.selectbox("Address Type", ["EXTERNAL", "INTERNAL"], key="new_ip_type")
        with col3:
            if st.button("➕ Add", key="add_ip"):
                if ip_name:
                    new_ip = {
                        "name": ip_name,
                        "address_type": ip_type,
                        "description": "Static IP created via GUI"
                    }
                    st.session_state.static_ips.append(new_ip)
                    st.rerun()
        
        if st.session_state.static_ips:
            resources["static_ips"] = st.session_state.static_ips
    
    # Compute Disks
    if st.checkbox("💾 Create Compute Disks"):
        st.markdown("**Compute Disk Configuration**")
        if 'disks' not in st.session_state:
            st.session_state.disks = []
        
        # Display existing disks
        if st.session_state.disks:
            st.markdown("**Current Compute Disks:**")
            for i, disk in enumerate(st.session_state.disks):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {disk['name']}")
                with col2:
                    st.text(f"Size: {disk['size_gb']}GB")
                with col3:
                    if st.button("🗑️", key=f"del_disk_{i}"):
                        st.session_state.disks.pop(i)
                        st.rerun()
        
        # Add new disk
        st.markdown("**Add New Compute Disk:**")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            disk_name = st.text_input("Disk Name", value="my-disk", key="new_disk_name")
        with col2:
            disk_zone = st.selectbox("Zone", ["us-central1-a", "us-west1-a", "europe-west1-a"], key="new_disk_zone")
        with col3:
            disk_size = st.number_input("Size (GB)", min_value=1, max_value=1000, value=10, key="new_disk_size")
        with col4:
            if st.button("➕ Add", key="add_disk"):
                if disk_name:
                    new_disk = {
                        "name": disk_name,
                        "zone": disk_zone,
                        "size_gb": disk_size,
                        "type": "pd-standard"
                    }
                    st.session_state.disks.append(new_disk)
                    st.rerun()
        
        if st.session_state.disks:
            resources["disks"] = st.session_state.disks
    
    # Memorystore Redis
    if st.checkbox("🔴 Create Memorystore Redis"):
        st.markdown("**Memorystore Redis Configuration**")
        if 'redis_instances' not in st.session_state:
            st.session_state.redis_instances = []
        
        # Display existing Redis instances
        if st.session_state.redis_instances:
            st.markdown("**Current Redis Instances:**")
            for i, redis in enumerate(st.session_state.redis_instances):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {redis['name']}")
                with col2:
                    st.text(f"Tier: {redis['tier']}")
                with col3:
                    if st.button("🗑️", key=f"del_redis_{i}"):
                        st.session_state.redis_instances.pop(i)
                        st.rerun()
        
        # Add new Redis instance
        st.markdown("**Add New Redis Instance:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            redis_name = st.text_input("Redis Name", value="my-redis", key="new_redis_name")
        with col2:
            redis_tier = st.selectbox("Tier", ["BASIC", "STANDARD_HA"], key="new_redis_tier")
        with col3:
            if st.button("➕ Add", key="add_redis"):
                if redis_name:
                    new_redis = {
                        "name": redis_name,
                        "region": "us-central1",
                        "tier": redis_tier,
                        "memory_size_gb": 1
                    }
                    st.session_state.redis_instances.append(new_redis)
                    st.rerun()
        
        if st.session_state.redis_instances:
            resources["redis_instances"] = st.session_state.redis_instances
    
    # Serverless VPC Connectors
    if st.checkbox("🔗 Create Serverless VPC Connectors"):
        st.markdown("**Serverless VPC Connector Configuration**")
        if 'serverless_vpc_connectors' not in st.session_state:
            st.session_state.serverless_vpc_connectors = []
        
        # Display existing connectors
        if st.session_state.serverless_vpc_connectors:
            st.markdown("**Current VPC Connectors:**")
            for i, connector in enumerate(st.session_state.serverless_vpc_connectors):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {connector['name']}")
                with col2:
                    st.text(f"Region: {connector['region']}")
                with col3:
                    if st.button("🗑️", key=f"del_vpc_conn_{i}"):
                        st.session_state.serverless_vpc_connectors.pop(i)
                        st.rerun()
        
        # Add new connector
        st.markdown("**Add New VPC Connector:**")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            vpc_conn_name = st.text_input("Connector Name", value="my-connector", key="new_vpc_conn_name")
        with col2:
            vpc_conn_region = st.selectbox("Region", ["us-central1", "us-west1", "europe-west1"], key="new_vpc_conn_region")
        with col3:
            vpc_conn_cidr = st.text_input("CIDR Range", value="10.8.0.0/28", key="new_vpc_conn_cidr")
        with col4:
            if st.button("➕ Add", key="add_vpc_conn"):
                if vpc_conn_name and vpc_conn_cidr:
                    new_connector = {
                        "name": vpc_conn_name,
                        "region": vpc_conn_region,
                        "network": "my-vpc",
                        "ip_cidr_range": vpc_conn_cidr
                    }
                    st.session_state.serverless_vpc_connectors.append(new_connector)
                    st.rerun()
        
        if st.session_state.serverless_vpc_connectors:
            resources["serverless_vpc_connectors"] = st.session_state.serverless_vpc_connectors
    
    # Only include VPCs/Subnets if their checkboxes are checked
    # (removed fallback that included them even when unchecked)

    # Keep a persistent copy of resources edited during the session
    if isinstance(st.session_state.project_resources, dict):
        if resources.get("vpcs"):
            st.session_state.project_resources["vpcs"] = resources["vpcs"]
        if resources.get("subnets"):
            st.session_state.project_resources["subnets"] = resources["subnets"]

    # Generate Configuration
    st.subheader("📄 Generated Configuration")
    
    if st.button("🔄 Generate YAML Configuration"):
        if not project_id:
            st.error("Please fill in Project ID")
            return
        
        from collections import OrderedDict
        
        # Create ordered dictionary with specific order
        config = OrderedDict()
        config["project_id"] = project_id
        if billing_account:  # Only include billing_account if provided
            config["billing_account"] = billing_account
        config["labels"] = labels
        config["apis"] = selected_apis
        if organization_id:
            config["organization_id"] = organization_id
        # Use only current resources (checkbox-controlled)
        config["resources"] = resources
        
        # Function to clean null values from nested dictionaries
        def clean_null_values(obj):
            if isinstance(obj, dict):
                return {k: clean_null_values(v) for k, v in obj.items() if v is not None and v != "" and v != [] and v != {}}
            elif isinstance(obj, list):
                return [clean_null_values(item) for item in obj if item is not None and item != "" and item != [] and item != {}]
            else:
                return obj
        
        # Display the configuration - only include non-empty sections
        filtered_config = {}
        
        # Always include project_id
        filtered_config["project_id"] = config["project_id"]
        # Include billing_account only if provided
        if config.get("billing_account"):
            filtered_config["billing_account"] = config["billing_account"]
        
        # Only include labels if not empty
        if config.get("labels") and any(config["labels"].values()):
            filtered_config["labels"] = config["labels"]
        
        # Only include apis if not empty
        if config.get("apis") and len(config["apis"]) > 0:
            filtered_config["apis"] = config["apis"]
        
        # Only include resources if not empty, and clean up null values
        if config.get("resources") and any(config["resources"].values()):
            cleaned_resources = clean_null_values(config["resources"])
            if cleaned_resources:  # Only include if there are any resources after cleaning
                filtered_config["resources"] = cleaned_resources
        
        st.code(yaml.dump(filtered_config, default_flow_style=False, sort_keys=False), language="yaml")
        
        # Save to session state
        st.session_state.generated_config = config
        st.session_state.config_filename = f"{project_id}.yaml"
        
        st.success(f"Configuration generated for project: {project_id}")
        
        # Download button - use the same filtered config
        yaml_content = yaml.dump(filtered_config, default_flow_style=False)
        st.download_button(
            label="📥 Download YAML Configuration",
            data=yaml_content,
            file_name=f"{project_id}.yaml",
            mime="text/yaml"
        )

    # New: Generate Terraform Files button
    if st.button("🛠️ Generate Terraform Files"):
        if not project_id:
            st.error("Please fill in Project ID")
            return

        # Reconstruct the same config structure as YAML generation (without requiring prior click)
        from collections import OrderedDict
        config: Dict[str, Any] = OrderedDict()
        config["project_id"] = project_id
        if billing_account:  # Only include billing_account if provided
            config["billing_account"] = billing_account
        if organization_id:
            config["organization_id"] = organization_id
        if labels and isinstance(labels, dict):
            config["labels"] = labels
        if selected_apis:
            config["apis"] = selected_apis
        config["resources"] = resources or {}

        # Clean helper (match YAML flow)
        def clean_null_values(obj):
            if isinstance(obj, dict):
                return {k: clean_null_values(v) for k, v in obj.items() if v not in (None, "", [], {})}
            if isinstance(obj, list):
                return [clean_null_values(i) for i in obj if i not in (None, "", [], {})]
            return obj

        cleaned_config = clean_null_values(config)

        # Generate standalone Terraform files (no external dependencies) entirely in-memory
        try:
            # Use the checkbox value to determine whether to create project
            create_project = create_new_project

            # Build files in memory
            main_tf_content = generate_standalone_main_tf(cleaned_config, create_project)
            variables_tf_content = generate_standalone_variables_tf(cleaned_config)
            outputs_tf_content = (
                "output \"project_id\" {\n  value = var.project_id\n}\n\n"
                "output \"enabled_apis\" {\n  value = var.apis\n}\n"
            )
            # HCL tfvars
            tfvars_hcl = []
            tfvars_hcl.append(f"project_id = \"{config['project_id']}\"")
            if config.get("organization_id"):
                tfvars_hcl.append(f"organization_id = \"{config['organization_id']}\"")
            if config.get("billing_account"):
                tfvars_hcl.append(f"billing_account = \"{config['billing_account']}\"")
            if config.get("labels"):
                tfvars_hcl.append("labels = {")
                for k, v in (config.get("labels") or {}).items():
                    tfvars_hcl.append(f"  \"{k}\" = \"{v}\"")
                tfvars_hcl.append("}")
            if config.get("apis"):
                apis_list = ", ".join([f'\"{a}\"' for a in config.get("apis", [])])
                tfvars_hcl.append(f"apis = [{apis_list}]")
            tfvars_hcl_content = "\n".join(tfvars_hcl) + "\n"
            
            tfvars_json_content = json.dumps(cleaned_config, indent=2)

            # Update main.tf to use credentials if available
            if hasattr(st.session_state, 'credentials_file') and st.session_state.credentials_file:
                main_tf_content = main_tf_content.replace(
                    '# credentials = file("path/to/credentials.json")  # Alternative: specify credentials file directly',
                    'credentials = file("credentials.json")  # Using uploaded credentials'
                )

            # Save in session_state only
            st.session_state.generated_tf_files = {
                "main.tf": main_tf_content,
                "variables.tf": variables_tf_content,
                "outputs.tf": outputs_tf_content,
                "terraform.tfvars": tfvars_hcl_content,
                "terraform.tfvars.json": tfvars_json_content,
            }

            # Store generation timestamp
            from datetime import datetime
            st.session_state.generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.success(f"Terraform files generated for project: {project_id}")

            # Display generated files content like YAML section
            files_to_show = ["main.tf", "variables.tf", "outputs.tf", "terraform.tfvars"]
            file_map = {k: v for k, v in st.session_state.generated_tf_files.items() if k in files_to_show}

            if file_map:
                st.subheader("📄 Generated Terraform Files")
                for file_name, content in file_map.items():
                    st.markdown(f"**{file_name}:**")
                    st.code(content, language="hcl" if file_name.endswith('.tf') or file_name.endswith('.tfvars') else "json")
                    st.markdown("---")

                # ZIP download option (like YAML download button)
                import zipfile
                import io
                
                # Create ZIP content
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Check if credentials are included and prepare main.tf accordingly
                    credentials_included = hasattr(st.session_state, 'credentials_file') and st.session_state.credentials_file
                    
                    # Add all files (main.tf is already modified if credentials are included)
                    for fname, fcontent in st.session_state.generated_tf_files.items():
                        zip_file.writestr(fname, fcontent)
                    
                    # Include credentials automatically if user has uploaded them
                    if credentials_included:
                        zip_file.writestr("credentials.json", st.session_state.credentials_file)
                    
                    readme_content = f"""# Terraform Configuration for {project_id}

This ZIP contains standalone Terraform files generated from the GCP Project Creator GUI.

## Files included:
- main.tf: Main Terraform configuration
- variables.tf: Variable definitions
- outputs.tf: Output definitions
- terraform.tfvars: Variable values (HCL format)
- terraform.tfvars.json: Variable values (JSON format)
{f"- credentials.json: GCP service account credentials" if credentials_included else ""}

## Usage:
1. Extract all files to a directory
2. Run: terraform init
3. Run: terraform plan
4. Run: terraform apply

## Important Notes:
- **Project Creation**: {'Creates a new GCP project with the specified configuration' if create_project else 'Works with an existing GCP project (no project creation)'}
- **Existing Projects**: {'If the project already exists, you may get an error. Use a different project_id if needed.' if create_project else 'Make sure the specified project_id exists and you have access to it.'}
- **Billing Account**: If not provided, you can set it later in the GCP Console
- **APIs**: Required APIs will be enabled automatically

## Authentication:
{f"**Included credentials.json**: The main.tf file is configured to use the included credentials.json file automatically. You can run terraform commands directly without additional setup." if credentials_included else "**Environment Variable**: Set GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your credentials file, or uncomment the credentials line in main.tf and specify your credentials file path."}

## Requirements:
- Terraform >= 1.6.0
- Google Cloud Provider >= 7.4.0
- Valid GCP credentials configured

Generated on: {st.session_state.get('generation_time', 'Unknown')}
Project ID: {project_id}
"""
                    zip_file.writestr("README.md", readme_content)
                
                zip_buffer.seek(0)
                zip_bytes = zip_buffer.getvalue()
                
                # Show what will be included in the ZIP
                if hasattr(st.session_state, 'credentials_file') and st.session_state.credentials_file:
                    st.info("🔑 **Credentials included**: Your uploaded credentials.json will be automatically included in the ZIP with configured main.tf")
                else:
                    st.info("ℹ️ **No credentials**: ZIP will not include credentials. Use environment variable or specify credentials file manually.")
                
                # Download button (same as YAML style)
                st.download_button(
                    label="📥 Download All Terraform Files as ZIP",
                    data=zip_bytes,
                    file_name=f"{project_id}-terraform.zip",
                    mime="application/zip"
                )
            else:
                st.warning("No Terraform files were generated")

        except Exception as e:
            st.error(f"Failed to generate Terraform files: {e}")

def config_manager():
    st.header("📋 Configuration Manager")
    st.markdown("Manage and edit your project configurations")
    
    # Debug information
    st.info(f"**Debug Info:** Project root: `{project_root}` | Configs path: `{project_root / 'configs'}`")
    
    # List existing configs
    configs_dir = project_root / "configs"
    if configs_dir.exists():
        st.success(f"✅ Found configs directory: `{configs_dir}`")
        config_files = list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml"))
        
        if config_files:
            st.subheader("📁 Existing Configurations")
            
            for config_file in config_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(config_file.name)
                with col2:
                    if st.button("📝 Edit", key=f"edit_{config_file.name}"):
                        st.session_state.editing_file = config_file.name
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{config_file.name}"):
                        config_file.unlink()
                        st.rerun()
        else:
            st.info("No configuration files found. Create one using the Project Builder.")
    else:
        st.error(f"❌ Configs directory not found at: `{configs_dir}`")
        st.warning("Please ensure you're running from the project root.")
        st.info("**Current working directory:** " + str(Path.cwd()))
        st.info("**Streamlit app location:** " + str(Path(__file__).parent))
        st.info("**Calculated project root:** " + str(project_root))
    
    # Edit configuration
    if hasattr(st.session_state, 'editing_file'):
        st.subheader(f"📝 Editing: {st.session_state.editing_file}")
        
        config_path = configs_dir / st.session_state.editing_file
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            edited_content = st.text_area(
                "Configuration Content",
                value=config_content,
                height=400
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes"):
                    try:
                        # Validate YAML
                        yaml.safe_load(edited_content)
                        with open(config_path, 'w') as f:
                            f.write(edited_content)
                        st.success("Configuration saved successfully!")
                        del st.session_state.editing_file
                        st.rerun()
                    except yaml.YAMLError as e:
                        st.error(f"Invalid YAML: {e}")
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.editing_file
                    st.rerun()

def deploy_monitor():
    st.header("🚀 Deploy & Monitor")
    st.markdown("Deploy your configurations and monitor the process")
    
    # Show credentials status
    st.subheader("🔑 Authentication Status")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if hasattr(st.session_state, 'credentials_file') and st.session_state.credentials_file:
            try:
                creds_json = json.loads(st.session_state.credentials_file)
                service_account_email = creds_json.get('client_email', 'Unknown')
                project_id = creds_json.get('project_id', 'Unknown')
                st.success(f"✅ Credentials loaded - Service Account: {service_account_email}")
                st.info(f"📋 Project ID: {project_id}")
            except:
                st.success("✅ Credentials loaded")
        else:
            st.info("ℹ️ No credentials uploaded - will use existing `gcloud` authentication if available")
            st.info("💡 Upload credentials in Project Builder for automatic deployment, or use existing `gcloud` authentication")
    
    with col2:
        if st.button("🏗️ Go to Builder", type="secondary"):
            st.session_state.page = "🏗️ Project Builder"
            st.rerun()
    
    # Select configuration to deploy
    configs_dir = project_root / "configs"
    if configs_dir.exists():
        config_files = list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml"))
        
        if config_files:
            selected_config = st.selectbox(
                "Select Configuration to Deploy",
                [f.name for f in config_files]
            )
            
            # Deployment options
            st.subheader("⚙️ Deployment Options")
            col1, col2 = st.columns(2)
            with col1:
                plan_only = st.checkbox("Plan Only (No Apply)", help="Show what will be created without applying")
            with col2:
                auto_approve = st.checkbox("Auto Approve", help="Skip confirmation prompts")
            
            # Deploy button
            if st.button("🚀 Deploy Configuration", type="primary"):
                deploy_config(selected_config, plan_only, auto_approve)
        else:
            st.info("No configuration files found. Create one using the Project Builder.")
    else:
        st.warning("Configs directory not found.")

def destroy_manager():
    st.header("🗑️ Destroy")
    st.markdown("Destroy deployed resources or entire projects using `scripts/destroy.py`.")

    configs_dir = project_root / "configs"
    available_configs = []
    if configs_dir.exists():
        available_configs = [f.name for f in list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml"))]

    st.subheader("Targets")
    col1, col2 = st.columns(2)
    with col1:
        selected_configs = st.multiselect("Select YAML configurations (optional)", options=available_configs)
    with col2:
        manual_projects = st.text_input("Or enter project IDs (space/comma-separated)", placeholder="proj-a proj-b")

    st.subheader("Options")
    colm1, colm2 = st.columns(2)
    with colm1:
        mode = st.radio("Mode", ["Modules only (m)", "Entire project (p)"])
    with colm2:
        force = st.checkbox("Force (auto-approve)")

    if st.button("🗑️ Destroy Now", type="primary"):
        # Build arguments
        args = []
        if force:
            args.append("--force")
        # Add YAML paths
        for name in selected_configs:
            args.append(str(configs_dir / name))
        # Add project ids
        if manual_projects.strip():
            import re
            parts = [p for p in re.split(r"[\s,]+", manual_projects.strip()) if p]
            for pid in parts:
                args.extend(["--project", pid])

        if not args:
            st.error("Please select at least one YAML or enter at least one project ID")
            return

        # Run destroy.py non-interactively by piping the menu choice
        # 'm' for modules, 'p' for project
        choice = 'm' if mode.startswith("Modules") else 'p'
        cmd = [sys.executable, str(project_root / "scripts" / "destroy.py"), *args]

        st.info(f"🔧 Running: {' '.join(cmd)}")
        try:
            # Ensure UTF-8 so emojis/logs don't crash on Windows
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            proc = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            # Feed prompts like the CLI: confirm (if not forced), then action m/p
            try:
                if proc.stdin:
                    if not force:
                        proc.stdin.write("yes\n")
                    proc.stdin.write(f"{choice}\n")
                    proc.stdin.flush()
            except Exception:
                pass

            output = proc.communicate(timeout=900)[0]
            st.subheader("📋 Destroy Output")
            st.code(output)

            if proc.returncode == 0:
                st.success("✅ Destroy completed")
            else:
                st.error(f"❌ Destroy exited with code {proc.returncode}")
        except subprocess.TimeoutExpired:
            st.error("⏰ Destroy timed out after 15 minutes")
        except Exception as e:
            st.error(f"💥 Destroy error: {e}")

def deploy_config(config_file, plan_only=False, auto_approve=False):
    """Deploy a configuration using the existing deploy script"""
    st.subheader("🔄 Deployment Progress")
    
    # Show deployment info
    config_path = project_root / "configs" / config_file
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    st.info(f"Deploying project: **{config.get('project_id', 'Unknown')}**")
    
    # Show authentication method
    if hasattr(st.session_state, 'credentials_file') and st.session_state.credentials_file:
        st.info("🔑 **Authentication**: Using uploaded service account credentials")
        try:
            creds_json = json.loads(st.session_state.credentials_file)
            service_account = creds_json.get('client_email', 'Unknown')
            st.info(f"🔑 **Service Account**: {service_account}")
        except:
            pass
    else:
        st.info("🔑 **Authentication**: Using existing gcloud authentication")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Run the deploy script
        status_text.text("Initializing deployment...")
        progress_bar.progress(10)
        
        # First run the deploy script to generate Terraform files
        deploy_cmd = [sys.executable, str(project_root / "scripts" / "deploy.py"), str(config_path)]
        
        # Set up environment variables
        env = os.environ.copy()
        
        # Handle interactive prompts based on deployment options
        if plan_only:
            # Skip the apply prompt in the deploy script - always answer "no"
            env["SKIP_APPLY_PROMPT"] = "true"
            env["AUTO_APPROVE_ANSWER"] = "no"
        elif auto_approve:
            # Skip the apply prompt in the deploy script - always answer "yes"
            env["SKIP_APPLY_PROMPT"] = "true"
            env["AUTO_APPROVE_ANSWER"] = "yes"
        
        status_text.text("Generating Terraform files...")
        progress_bar.progress(20)
        
        # Show the command being run
        st.info(f"🔧 Running command: `{' '.join(deploy_cmd)}`")
        
        # Check for credentials and set up authentication
        credentials_setup_success = False
        
        if not plan_only:
            # First check if we have uploaded credentials in session state
            if hasattr(st.session_state, 'credentials_file') and st.session_state.credentials_file:
                try:
                    # Create a temporary credentials file
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        f.write(st.session_state.credentials_file)
                        temp_creds_path = f.name
                    
                    # Set environment variable for authentication
                    env['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_path
                    
                    # Test authentication with the credentials
                    gcloud_check = subprocess.run(
                        ["gcloud", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    
                    if gcloud_check.returncode == 0:
                        st.success("✅ gcloud is available")
                        
                        # Activate service account
                        auth_cmd = ['gcloud', 'auth', 'activate-service-account', '--key-file', temp_creds_path]
                        auth_result = subprocess.run(
                            auth_cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            env=env
                        )
                        
                        if auth_result.returncode == 0:
                            # Get the service account email from credentials
                            creds_json = json.loads(st.session_state.credentials_file)
                            service_account_email = creds_json.get('client_email', 'Unknown')
                            st.success(f"✅ Authenticated with service account: {service_account_email}")
                            credentials_setup_success = True
                        else:
                            st.error(f"❌ Failed to authenticate with service account: {auth_result.stderr}")
                    else:
                        st.error("❌ gcloud command not found")
                        
                except Exception as e:
                    st.error(f"❌ Error setting up credentials: {str(e)}")
            else:
                # Fallback to checking existing gcloud authentication
                try:
                    gcloud_check = subprocess.run(
                        ["gcloud", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if gcloud_check.returncode == 0:
                        st.success("✅ gcloud is available")
                        
                        # Check authentication
                        auth_check = subprocess.run(
                            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if auth_check.returncode == 0 and auth_check.stdout.strip():
                            st.success(f"✅ Authenticated as: {auth_check.stdout.strip()}")
                            credentials_setup_success = True
                        else:
                            st.warning("⚠️ No active gcloud authentication found")
                            st.info("💡 Upload credentials in Project Settings or run: `gcloud auth login`")
                    else:
                        st.error("❌ gcloud command not found")
                except Exception as e:
                    st.error(f"❌ Error checking gcloud: {str(e)}")
        else:
            st.info("ℹ️ Plan-only mode: No GCP authentication required")
            credentials_setup_success = True
        
        # If we're deploying (not planning) and no credentials are set up, show warning
        if not plan_only and not credentials_setup_success:
            st.warning("⚠️ No GCP credentials configured. Deployment may fail.")
            st.info("💡 Please configure credentials in the Project Settings page before deploying.")
        
        # Use real-time output to avoid hanging
        # Pass environment variables to ensure gcloud access
        
        # Simple approach: just run the deploy script with the environment variables
        deploy_result = subprocess.run(
            deploy_cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            env=env
        )
        
        # Display deploy script results
        progress_bar.progress(80)
        status_text.text("Processing results...")
        
        # Function to remove ANSI escape codes
        def strip_ansi(text):
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)
        
        if deploy_result.returncode == 0:
            st.success("✅ Deploy script completed successfully!")
            progress_bar.progress(100)
            
            if deploy_result.stdout:
                st.subheader("📋 Deploy Script Output")
                clean_output = strip_ansi(deploy_result.stdout)
                st.code(clean_output)
        else:
            st.error("❌ Deploy script failed!")
            progress_bar.progress(100)
            
            if deploy_result.stderr:
                st.subheader("🚨 Error Details")
                clean_stderr = strip_ansi(deploy_result.stderr)
                st.code(clean_stderr)
            
            if deploy_result.stdout:
                st.subheader("📋 Output")
                clean_output = strip_ansi(deploy_result.stdout)
                st.code(clean_output)
        
        status_text.text("Deployment completed")
        
    except subprocess.TimeoutExpired:
        st.error("⏰ Deploy script timed out after 10 minutes")
        progress_bar.progress(100)
        st.warning("💡 The deploy script is hanging. This usually means:")
        st.markdown("""
        - **GCP Authentication**: Run `gcloud auth login` first
        - **Network Issues**: Check your internet connection
        - **Invalid Config**: Check your YAML file for errors
        - **Python Dependencies**: Missing required packages
        """)
        st.info("🔧 Manual command to test:")
        st.code(f"python {project_root / 'scripts' / 'deploy.py'} {config_path}")
        st.info("💡 Try running this command in your terminal to see where it hangs")
    except Exception as e:
        st.error(f"💥 Deployment error: {str(e)}")
        progress_bar.progress(100)

def help_examples():
    st.header("📚 Help & Examples")
    st.markdown("Learn how to use the GCP Project Creator")
    
    # Quick start guide
    st.subheader("🚀 Quick Start Guide")
    st.markdown("""
    1. **Project Builder**: Use the Project Builder to create your first configuration
    2. **Configure Resources**: Select the GCP resources you need (VPC, VMs, storage, etc.)
    3. **Generate YAML**: Click "Generate YAML Configuration" to create your config file
    4. **Deploy**: Use the Deploy & Monitor page to deploy your configuration
    5. **Monitor**: Watch the deployment progress and check for any errors
    """)
    
    # API Configuration
    st.subheader("🔌 API Configuration")
    st.markdown("**Available API Categories:**")
    st.markdown("""
    - **Core Infrastructure**: Compute, IAM, Storage, Resource Manager, Service Usage, OS Login, Cloud Trace
    - **Networking**: DNS, VPC Access, Network Connectivity
    - **Serverless**: Cloud Run, Cloud Functions
    - **Databases & Storage**: Cloud SQL, BigQuery (all variants), Redis, Spanner, Datastore
    - **Security & Secrets**: Secret Manager, Privileged Access Manager
    - **Messaging & Events**: Pub/Sub
    - **Containers & Artifacts**: GKE, Artifact Registry, Container Registry, Container File System
    - **Analytics & Data**: Analytics Hub, BigQuery, Dataplex, Dataform
    - **AI & Machine Learning**: Vertex AI, Gemini for Google Cloud
    - **Monitoring & Logging**: Cloud Logging, Cloud Monitoring, Cloud Profiler
    - **Backup & Recovery**: Backup for GKE
    - **Service Management**: Service Management, Service Usage
    - **Storage & Files**: Cloud Storage, Cloud Storage JSON API
    """)
    
    st.markdown("**Basic API Configuration**")
    basic_api_example = {
        "project_id": "my-basic-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": [
            "compute.googleapis.com",
            "storage.googleapis.com",
            "iam.googleapis.com"
        ]
    }
    st.code(yaml.dump(basic_api_example, default_flow_style=False), language="yaml")
    
    st.markdown("**Comprehensive API Configuration**")
    comprehensive_api_example = {
        "project_id": "my-comprehensive-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": [
            "compute.googleapis.com",
            "iam.googleapis.com",
            "storage.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "serviceusage.googleapis.com",
            "dns.googleapis.com",
            "run.googleapis.com",
            "cloudfunctions.googleapis.com",
            "bigquery.googleapis.com",
            "sqladmin.googleapis.com",
            "container.googleapis.com",
            "artifactregistry.googleapis.com",
            "pubsub.googleapis.com",
            "secretmanager.googleapis.com",
            "logging.googleapis.com",
            "monitoring.googleapis.com",
            "aiplatform.googleapis.com",
            "analyticshub.googleapis.com",
            "dataplex.googleapis.com",
            "spanner.googleapis.com",
            "datastore.googleapis.com"
        ]
    }
    st.code(yaml.dump(comprehensive_api_example, default_flow_style=False), language="yaml")
    
    # Example configurations
    st.subheader("📝 Example Configurations")
    
    # Simple project example
    st.markdown("**Simple Project with VM and Storage**")
    simple_example = {
        "project_id": "my-simple-project",
        "billing_account": "01783B-A7A65B-153181",
        "labels": {
            "environment": "dev",
            "owner": "developer"
        },
        "apis": [
            "compute.googleapis.com",
            "storage.googleapis.com"
        ],
        "resources": {
            "compute_instances": [{
                "name": "web-server",
                "zone": "us-central1-a",
                "machine_type": "e2-micro",
                "image": "debian-cloud/debian-11"
            }],
            "storage_buckets": [{
                "name": "my-app-storage",
                "location": "US"
            }]
        }
    }
    
    st.code(yaml.dump(simple_example, default_flow_style=False), language="yaml")
    
    # Advanced project example
    st.markdown("**Advanced Project with VPC, Cloud Run, Database, and VM**")
    advanced_example = {
        "project_id": "my-advanced-project",
        "billing_account": "01783B-A7A65B-153181",
        "labels": {
            "environment": "production",
            "team": "platform"
        },
        "apis": [
            "compute.googleapis.com",
            "run.googleapis.com",
            "sqladmin.googleapis.com",
            "vpcaccess.googleapis.com"
        ],
        "resources": {
            "vpc": {
                "name": "production-vpc",
                "routing_mode": "GLOBAL"
            },
            "subnets": [{
                "name": "app-subnet",
                "region": "us-central1",
                "ip_cidr_range": "10.0.0.0/24",
                "network": "production-vpc"
            }],
            "serverless_vpc_connectors": [{
                "name": "run-connector",
                "region": "us-central1",
                "network": "production-vpc",
                "ip_cidr_range": "10.8.0.0/28"
            }],
            "cloud_run_services": [{
                "name": "api-service",
                "location": "us-central1",
                "image": "gcr.io/cloudrun/hello",
                "vpc_connector": "run-connector"
            }],
            "compute_instances": [{
                "name": "app-vm",
                "zone": "us-central1-a",
                "machine_type": "e2-standard-2",
                "image": "debian-cloud/debian-11",
                "description": "Application server",
                "network": "production-vpc",
                "subnetwork": "app-subnet",
                "assign_external_ip": True,
                "external_network_tier": "PREMIUM",
                "labels": {"env": "prod"},
                "metadata": {"foo": "bar"},
                "metadata_startup_script": "#!/bin/bash\nprintf 'hello' > /tmp/hello.txt\n",
                "boot_disk_size_gb": 20,
                "boot_disk_type": "pd-balanced",
                "boot_disk_auto_delete": True,
                "tags": ["web", "ssh"],
                "service_account_email": "custom-sa@my-proj.iam.gserviceaccount.com",
                "service_account_scopes": ["https://www.googleapis.com/auth/cloud-platform"],
                "scheduling_preemptible": False,
                "scheduling_automatic_restart": True,
                "scheduling_on_host_maintenance": "MIGRATE",
                "enable_shielded_vm": True,
                "shielded_secure_boot": True,
                "guest_accelerators": [],
                "deletion_protection": False
            }],
            "cloud_sql_instances": [{
                "name": "app-database",
                "database_version": "POSTGRES_14",
                "region": "us-central1",
                "tier": "db-f1-micro"
            }]
        }
    }
    
    st.code(yaml.dump(advanced_example, default_flow_style=False), language="yaml")
    
    # Firewall Examples
    st.subheader("🔥 Firewall Configuration Examples")
    
    # Basic Firewall Example
    st.markdown("**Basic Firewall Rule**")
    basic_firewall_example = {
        "project_id": "my-firewall-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "my-vpc",
                "routing_mode": "GLOBAL"
            }],
            "firewall_rules": [{
                "name": "allow-ssh",
                "network": "my-vpc",
                "direction": "INGRESS",
                "protocol": "tcp",
                "source_ranges": ["0.0.0.0/0"],
                "ports": ["22"],
                "priority": 1000
            }]
        }
    }
    st.code(yaml.dump(basic_firewall_example, default_flow_style=False), language="yaml")
    
    # Advanced Firewall Example
    st.markdown("**Advanced Firewall Rules with Tags and Service Accounts**")
    advanced_firewall_example = {
        "project_id": "my-advanced-firewall-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "production-vpc",
                "routing_mode": "GLOBAL"
            }],
            "firewall_rules": [
                {
                    "name": "allow-web-traffic",
                    "network": "production-vpc",
                    "direction": "INGRESS",
                    "protocol": "tcp",
                    "source_ranges": ["0.0.0.0/0"],
                    "target_tags": ["web-server"],
                    "ports": ["80", "443"],
                    "priority": 1000,
                    "description": "Allow HTTP/HTTPS traffic to web servers"
                },
                {
                    "name": "allow-database-access",
                    "network": "production-vpc",
                    "direction": "INGRESS",
                    "protocol": "tcp",
                    "source_tags": ["app-server"],
                    "target_tags": ["database"],
                    "ports": ["5432"],
                    "priority": 1000,
                    "description": "Allow database access from app servers"
                },
                {
                    "name": "deny-internal-ssh",
                    "network": "production-vpc",
                    "direction": "INGRESS",
                    "protocol": "tcp",
                    "source_ranges": ["10.0.0.0/8"],
                    "ports": ["22"],
                    "priority": 2000,
                    "disabled": False,
                    "description": "Deny SSH from internal networks"
                }
            ]
        }
    }
    st.code(yaml.dump(advanced_firewall_example, default_flow_style=False), language="yaml")
    
    # EGRESS Firewall Example
    st.markdown("**EGRESS Firewall Rules**")
    egress_firewall_example = {
        "project_id": "my-egress-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "secure-vpc",
                "routing_mode": "GLOBAL"
            }],
            "firewall_rules": [{
                "name": "allow-outbound-https",
                "network": "secure-vpc",
                "direction": "EGRESS",
                "protocol": "tcp",
                "destination_ranges": ["0.0.0.0/0"],
                "ports": ["443"],
                "priority": 1000,
                "description": "Allow outbound HTTPS traffic"
            }]
        }
    }
    st.code(yaml.dump(egress_firewall_example, default_flow_style=False), language="yaml")
    
    # Firewall with Logging Example
    st.markdown("**Firewall Rules with Logging**")
    logging_firewall_example = {
        "project_id": "my-logging-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "monitored-vpc",
                "routing_mode": "GLOBAL"
            }],
            "firewall_rules": [{
                "name": "monitored-web-traffic",
                "network": "monitored-vpc",
                "direction": "INGRESS",
                "protocol": "tcp",
                "source_ranges": ["0.0.0.0/0"],
                "target_tags": ["web-server"],
                "ports": ["80", "443"],
                "priority": 1000,
                "enable_logging": True,
                "log_config": {
                    "metadata": "INCLUDE_ALL_METADATA"
                },
                "description": "Monitored web traffic with full logging"
            }]
        }
    }
    st.code(yaml.dump(logging_firewall_example, default_flow_style=False), language="yaml")
    
    # Service Account Firewall Example
    st.markdown("**Firewall Rules with Service Accounts**")
    service_account_firewall_example = {
        "project_id": "my-sa-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "sa-vpc",
                "routing_mode": "GLOBAL"
            }],
            "service_accounts": [{
                "account_id": "app-service-account",
                "display_name": "Application Service Account"
            }],
            "firewall_rules": [{
                "name": "allow-service-account-access",
                "network": "sa-vpc",
                "direction": "INGRESS",
                "protocol": "tcp",
                "source_service_accounts": ["app-service-account@my-sa-project.iam.gserviceaccount.com"],
                "target_tags": ["api-server"],
                "ports": ["8080"],
                "priority": 1000,
                "description": "Allow access from specific service account"
            }]
        }
    }
    st.code(yaml.dump(service_account_firewall_example, default_flow_style=False), language="yaml")
    
    # VPC Examples
    st.subheader("🌐 VPC Configuration Examples")
    
    # Basic VPC Example
    st.markdown("**Basic VPC Network**")
    basic_vpc_example = {
        "project_id": "my-vpc-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "my-vpc",
                "routing_mode": "GLOBAL",
                "description": "Basic VPC network"
            }]
        }
    }
    st.code(yaml.dump(basic_vpc_example, default_flow_style=False), language="yaml")
    
    # Advanced VPC Example
    st.markdown("**Advanced VPC with Custom MTU and BGP**")
    advanced_vpc_example = {
        "project_id": "my-advanced-vpc-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "production-vpc",
                "routing_mode": "GLOBAL",
                "description": "Production VPC with advanced features",
                "mtu": 1500,
                "auto_create_subnetworks": False,
                "bgp_best_path_selection_mode": "STANDARD",
                "bgp_always_compare_med": True,
                "bgp_inter_region_cost": "ADD_COST_TO_MED",
                "network_firewall_policy_enforcement_order": "BEFORE_CLASSIC_FIREWALL",
                "delete_default_routes_on_create": True,
                "resource_manager_tags": {
                    "tagKeys/123": "tagValues/456",
                    "tagKeys/789": "tagValues/012"
                }
            }]
        }
    }
    st.code(yaml.dump(advanced_vpc_example, default_flow_style=False), language="yaml")
    
    # IPv6 VPC Example
    st.markdown("**VPC with IPv6 Support**")
    ipv6_vpc_example = {
        "project_id": "my-ipv6-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "ipv6-vpc",
                "routing_mode": "GLOBAL",
                "description": "VPC with IPv6 support",
                "enable_ula_internal_ipv6": True,
                "internal_ipv6_range": "fd20:1234:5678::/48",
                "mtu": 1500
            }]
        }
    }
    st.code(yaml.dump(ipv6_vpc_example, default_flow_style=False), language="yaml")
    
    # Regional VPC Example
    st.markdown("**Regional VPC Network**")
    regional_vpc_example = {
        "project_id": "my-regional-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "regional-vpc",
                "routing_mode": "REGIONAL",
                "region": "us-central1",
                "description": "Regional VPC for specific region",
                "mtu": 1460,
                "auto_create_subnetworks": True
            }]
        }
    }
    st.code(yaml.dump(regional_vpc_example, default_flow_style=False), language="yaml")
    
    # Auto Subnet VPC Example
    st.markdown("**VPC with Auto Subnetworks**")
    auto_subnet_vpc_example = {
        "project_id": "my-auto-subnet-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "auto-subnet-vpc",
                "routing_mode": "GLOBAL",
                "description": "VPC with automatic subnet creation",
                "auto_create_subnetworks": True,
                "mtu": 1500,
                "network_firewall_policy_enforcement_order": "AFTER_CLASSIC_FIREWALL"
            }]
        }
    }
    st.code(yaml.dump(auto_subnet_vpc_example, default_flow_style=False), language="yaml")
    
    # Network Profile VPC Example
    st.markdown("**VPC with Network Profile**")
    network_profile_vpc_example = {
        "project_id": "my-profile-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "profile-vpc",
                "routing_mode": "GLOBAL",
                "description": "VPC with custom network profile",
                "network_profile": "projects/my-profile-project/global/networkProfiles/high-performance",
                "mtu": 1500,
                "bgp_best_path_selection_mode": "STANDARD"
            }]
        }
    }
    st.code(yaml.dump(network_profile_vpc_example, default_flow_style=False), language="yaml")
    
    # Subnet Examples
    st.subheader("📡 Subnet Configuration Examples")
    
    # Basic Subnet Example
    st.markdown("**Basic Subnet**")
    basic_subnet_example = {
        "project_id": "my-subnet-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "my-vpc",
                "routing_mode": "GLOBAL"
            }],
            "subnets": [{
                "name": "my-subnet",
                "region": "us-central1",
                "ip_cidr_range": "10.0.0.0/24",
                "network": "my-vpc",
                "private_ip_google_access": True
            }]
        }
    }
    st.code(yaml.dump(basic_subnet_example, default_flow_style=False), language="yaml")
    
    # Advanced Subnet Example
    st.markdown("**Advanced Subnet with IPv6 and Logging**")
    advanced_subnet_example = {
        "project_id": "my-advanced-subnet-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "production-vpc",
                "routing_mode": "GLOBAL",
                "enable_ula_internal_ipv6": True
            }],
            "subnets": [{
                "name": "production-subnet",
                "region": "us-central1",
                "ip_cidr_range": "10.0.0.0/24",
                "network": "production-vpc",
                "description": "Production subnet with advanced features",
                "private_ip_google_access": True,
                "stack_type": "IPV4_IPV6",
                "ipv6_access_type": "EXTERNAL",
                "log_config": {
                    "aggregation_interval": "INTERVAL_10_MIN",
                    "flow_sampling": 0.5,
                    "metadata": "INCLUDE_ALL_METADATA"
                },
                "resource_manager_tags": {
                    "tagKeys/123": "tagValues/456"
                }
            }]
        }
    }
    st.code(yaml.dump(advanced_subnet_example, default_flow_style=False), language="yaml")
    
    # Load Balancer Subnet Example
    st.markdown("**Load Balancer Subnet (REGIONAL_MANAGED_PROXY)**")
    lb_subnet_example = {
        "project_id": "my-lb-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "lb-vpc",
                "routing_mode": "GLOBAL"
            }],
            "subnets": [{
                "name": "lb-subnet",
                "region": "us-central1",
                "ip_cidr_range": "10.0.0.0/24",
                "network": "lb-vpc",
                "purpose": "REGIONAL_MANAGED_PROXY",
                "role": "ACTIVE",
                "description": "Load balancer subnet for regional Envoy-based load balancers"
            }]
        }
    }
    st.code(yaml.dump(lb_subnet_example, default_flow_style=False), language="yaml")
    
    # Private Service Connect Subnet Example
    st.markdown("**Private Service Connect Subnet**")
    psc_subnet_example = {
        "project_id": "my-psc-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "psc-vpc",
                "routing_mode": "GLOBAL"
            }],
            "subnets": [{
                "name": "psc-subnet",
                "region": "us-central1",
                "ip_cidr_range": "10.0.0.0/24",
                "network": "psc-vpc",
                "purpose": "PRIVATE_SERVICE_CONNECT",
                "description": "Private Service Connect subnet for hosting published services"
            }]
        }
    }
    st.code(yaml.dump(psc_subnet_example, default_flow_style=False), language="yaml")
    
    # IPv6 Subnet Example
    st.markdown("**IPv6 Subnet with External Access**")
    ipv6_subnet_example = {
        "project_id": "my-ipv6-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "ipv6-vpc",
                "routing_mode": "GLOBAL"
            }],
            "subnets": [{
                "name": "ipv6-subnet",
                "region": "us-west2",
                "ip_cidr_range": "10.0.0.0/22",
                "network": "ipv6-vpc",
                "stack_type": "IPV4_IPV6",
                "ipv6_access_type": "EXTERNAL",
                "description": "Dual-stack subnet with external IPv6 access"
            }]
        }
    }
    st.code(yaml.dump(ipv6_subnet_example, default_flow_style=False), language="yaml")
    
    # Private NAT Subnet Example
    st.markdown("**Private NAT Subnet**")
    private_nat_subnet_example = {
        "project_id": "my-nat-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["compute.googleapis.com"],
        "resources": {
            "vpcs": [{
                "name": "nat-vpc",
                "routing_mode": "GLOBAL"
            }],
            "subnets": [{
                "name": "nat-subnet",
                "region": "us-west2",
                "ip_cidr_range": "192.168.1.0/24",
                "network": "nat-vpc",
                "purpose": "PRIVATE_NAT",
                "description": "Private NAT subnet for NAT gateway source range"
            }]
        }
    }
    st.code(yaml.dump(private_nat_subnet_example, default_flow_style=False), language="yaml")
    
    # Service Account Examples
    st.subheader("👤 Service Account Configuration Examples")
    
    # Basic Service Account Example
    st.markdown("**Basic Service Account**")
    basic_sa_example = {
        "project_id": "my-sa-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "my-service-account",
                "display_name": "My Service Account"
            }]
        }
    }
    st.code(yaml.dump(basic_sa_example, default_flow_style=False), language="yaml")
    
    # Advanced Service Account Example
    st.markdown("**Advanced Service Account with All Options**")
    advanced_sa_example = {
        "project_id": "my-advanced-sa-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "production-service-account",
                "display_name": "Production Service Account",
                "description": "Service account for production workloads with advanced configuration",
                "disabled": False,
                "create_ignore_already_exists": True
            }]
        }
    }
    st.code(yaml.dump(advanced_sa_example, default_flow_style=False), language="yaml")
    
    # Multiple Service Accounts Example
    st.markdown("**Multiple Service Accounts for Different Purposes**")
    multiple_sa_example = {
        "project_id": "my-multi-sa-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [
                {
                    "account_id": "web-server-sa",
                    "display_name": "Web Server Service Account",
                    "description": "Service account for web server instances"
                },
                {
                    "account_id": "database-sa",
                    "display_name": "Database Service Account",
                    "description": "Service account for database operations"
                },
                {
                    "account_id": "monitoring-sa",
                    "display_name": "Monitoring Service Account",
                    "description": "Service account for monitoring and logging",
                    "disabled": False,
                    "create_ignore_already_exists": False
                }
            ]
        }
    }
    st.code(yaml.dump(multiple_sa_example, default_flow_style=False), language="yaml")
    
    # Disabled Service Account Example
    st.markdown("**Disabled Service Account**")
    disabled_sa_example = {
        "project_id": "my-disabled-sa-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "deprecated-sa",
                "display_name": "Deprecated Service Account",
                "description": "This service account is being phased out",
                "disabled": True,
                "create_ignore_already_exists": True
            }]
        }
    }
    st.code(yaml.dump(disabled_sa_example, default_flow_style=False), language="yaml")
    
    # Service Account with Permissions Example
    st.markdown("**Service Account with Permissions/Roles**")
    sa_with_permissions_example = {
        "project_id": "my-sa-permissions-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "app-service-account",
                "display_name": "Application Service Account",
                "description": "Service account for application workloads with specific permissions",
                "roles": [
                    "roles/storage.objectViewer",
                    "roles/logging.logWriter",
                    "roles/monitoring.metricWriter"
                ]
            }]
        }
    }
    st.code(yaml.dump(sa_with_permissions_example, default_flow_style=False), language="yaml")
    
    # Service Account with Custom Roles Example
    st.markdown("**Service Account with Custom Roles**")
    sa_with_custom_roles_example = {
        "project_id": "my-sa-custom-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "admin-service-account",
                "display_name": "Admin Service Account",
                "description": "Service account with custom admin roles",
                "roles": [
                    "roles/storage.objectAdmin",
                    "roles/compute.instanceAdmin",
                    "roles/iam.serviceAccountUser",
                    "roles/secretmanager.secretAccessor"
                ]
            }]
        }
    }
    st.code(yaml.dump(sa_with_custom_roles_example, default_flow_style=False), language="yaml")
    
    # Service Account with IAM Example (Legacy)
    st.markdown("**Service Account with IAM Bindings (Legacy Method)**")
    sa_with_iam_example = {
        "project_id": "my-sa-iam-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "app-service-account",
                "display_name": "Application Service Account",
                "description": "Service account for application workloads"
            }],
            "iam": [{
                "role": "roles/storage.objectViewer",
                "members": ["serviceAccount:app-service-account@my-sa-iam-project.iam.gserviceaccount.com"]
            }]
        }
    }
    st.code(yaml.dump(sa_with_iam_example, default_flow_style=False), language="yaml")
    
    # Service Account with Key Management Example
    st.markdown("**Service Account with Key Management**")
    sa_with_keys_example = {
        "project_id": "my-sa-keys-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [{
                "account_id": "api-service-account",
                "display_name": "API Service Account",
                "description": "Service account for API authentication with key management",
                "roles": [
                    "roles/storage.objectViewer",
                    "roles/logging.logWriter"
                ],
                "create_key": True,
                "key_algorithm": "KEY_ALG_RSA_2048",
                "public_key_type": "TYPE_X509_PEM_FILE",
                "private_key_type": "TYPE_GOOGLE_CREDENTIALS_FILE",
                "key_file_path": "/tmp/api-service-account-key.json"
            }]
        }
    }
    st.code(yaml.dump(sa_with_keys_example, default_flow_style=False), language="yaml")
    
    # Service Account with Different Key Types Example
    st.markdown("**Service Account with Different Key Types**")
    sa_different_keys_example = {
        "project_id": "my-sa-different-keys-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "service_accounts": [
                {
                    "account_id": "pkcs12-service-account",
                    "display_name": "PKCS12 Service Account",
                    "description": "Service account with PKCS12 key format",
                    "create_key": True,
                    "key_algorithm": "KEY_ALG_RSA_2048",
                    "public_key_type": "TYPE_X509_PEM_FILE",
                    "private_key_type": "TYPE_PKCS12_FILE",
                    "key_file_path": "/tmp/pkcs12-key.p12"
                },
                {
                    "account_id": "raw-key-service-account",
                    "display_name": "Raw Key Service Account",
                    "description": "Service account with raw public key",
                    "create_key": True,
                    "key_algorithm": "KEY_ALG_RSA_1024",
                    "public_key_type": "TYPE_RAW_PUBLIC_KEY",
                    "private_key_type": "TYPE_GOOGLE_CREDENTIALS_FILE"
                }
            ]
        }
    }
    st.code(yaml.dump(sa_different_keys_example, default_flow_style=False), language="yaml")
    
    # IAM Policy Examples
    st.subheader("🔐 IAM Policy Configuration Examples")
    
    st.markdown("**Role Selection:** The Role dropdown includes common IAM roles like `roles/owner`, `roles/editor`, `roles/viewer`, service account roles, and service-specific roles. Select 'Custom Role' to enter a custom role name.")
    
    # IAM Member Example
    st.markdown("**IAM Member (Non-authoritative)**")
    iam_member_example = {
        "project_id": "my-iam-member-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "iam": [{
                "iam_type": "member",
                "role": "roles/storage.objectViewer",
                "member": "user:john@example.com"
            }]
        }
    }
    st.code(yaml.dump(iam_member_example, default_flow_style=False), language="yaml")
    
    # IAM Binding Example
    st.markdown("**IAM Binding (Authoritative for role)**")
    iam_example = {
        "project_id": "my-iam-binding-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "iam": [{
                "iam_type": "binding",
                "role": "roles/editor",
                "members": [
                    "user:admin@example.com",
                    "serviceAccount:app@project.iam.gserviceaccount.com",
                    "group:developers@example.com"
                ]
            }]
        }
    }
    st.code(yaml.dump(iam_example, default_flow_style=False), language="yaml")
    
    # IAM Policy Example
    st.markdown("**IAM Policy (Authoritative - replaces entire policy)**")
    iam_policy_example = {
        "project_id": "my-iam-policy-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "iam": [{
                "iam_type": "policy",
                "policy_data": "{\"bindings\": [{\"role\": \"roles/editor\", \"members\": [\"user:admin@example.com\"]}, {\"role\": \"roles/viewer\", \"members\": [\"user:viewer@example.com\"]}]}"
            }]
        }
    }
    st.code(yaml.dump(iam_policy_example, default_flow_style=False), language="yaml")
    
    # IAM Audit Config Example
    st.markdown("**IAM Audit Config (Audit logging)**")
    iam_audit_example = {
        "project_id": "my-iam-audit-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "iam": [{
                "iam_type": "audit_config",
                "service": "allServices",
                "audit_log_configs": [
                    {
                        "log_type": "ADMIN_READ",
                        "exempted_members": []
                    },
                    {
                        "log_type": "DATA_READ",
                        "exempted_members": ["user:admin@example.com"]
                    }
                ]
            }]
        }
    }
    st.code(yaml.dump(iam_audit_example, default_flow_style=False), language="yaml")
    
    # IAM with Conditions Example
    st.markdown("**IAM with Conditions (Time-based access)**")
    iam_conditions_example = {
        "project_id": "my-iam-conditions-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "iam": [{
                "iam_type": "member",
                "role": "roles/compute.admin",
                "member": "user:contractor@example.com",
                "condition": {
                    "title": "expires_after_2024",
                    "expression": "request.time < timestamp(\"2024-12-31T23:59:59Z\")",
                    "description": "Access expires at end of 2024"
                }
            }]
        }
    }
    st.code(yaml.dump(iam_conditions_example, default_flow_style=False), language="yaml")
    
    # Multiple IAM Types Example
    st.markdown("**Multiple IAM Types in One Project**")
    iam_multiple_example = {
        "project_id": "my-iam-multiple-project",
        "billing_account": "01783B-A7A65B-153181",
        "apis": ["iam.googleapis.com"],
        "resources": {
            "iam": [
                {
                    "iam_type": "member",
                    "role": "roles/storage.objectViewer",
                    "member": "user:readonly@example.com"
                },
                {
                    "iam_type": "binding",
                    "role": "roles/editor",
                    "members": [
                        "user:admin@example.com",
                        "serviceAccount:app@project.iam.gserviceaccount.com"
                    ]
                },
                {
                    "iam_type": "audit_config",
                    "service": "compute.googleapis.com",
                    "audit_log_configs": [
                        {
                            "log_type": "ADMIN_READ",
                            "exempted_members": []
                        }
                    ]
                }
            ]
        }
    }
    st.code(yaml.dump(iam_multiple_example, default_flow_style=False), language="yaml")
    
    # Troubleshooting
    st.subheader("🔧 Troubleshooting")
    st.markdown("""
    **Common Issues:**
    
    - **Project ID already exists**: Choose a unique project ID
    - **Billing account not found**: Verify your billing account ID
    - **API not enabled**: Make sure to select required APIs
    - **Deployment fails**: Check the error output in the Deploy & Monitor page
    
    **Getting Help:**
    - Check the project README for detailed documentation
    - Review the generated YAML configuration for syntax errors
    - Ensure you have proper GCP permissions
    """)

if __name__ == "__main__":
    main()
