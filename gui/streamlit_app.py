import streamlit as st
import yaml
import json
import subprocess
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

st.set_page_config(
    page_title="GCP Project Creator",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("☁️ GCP Project Creator")
    st.markdown("Create and deploy Google Cloud Platform projects with a simple GUI interface")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "🏗️ Project Builder",
        "📋 Configuration Manager", 
        "🚀 Deploy & Monitor",
        "📚 Help & Examples"
    ])
    
    if page == "🏗️ Project Builder":
        project_builder()
    elif page == "📋 Configuration Manager":
        config_manager()
    elif page == "🚀 Deploy & Monitor":
        deploy_monitor()
    elif page == "📚 Help & Examples":
        help_examples()

def project_builder():
    st.header("🏗️ Project Builder")
    st.markdown("Configure your GCP project step by step")
    
    # Project Settings
    st.subheader("📋 Project Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        project_id = st.text_input(
            "Project ID", 
            placeholder="my-awesome-project-123",
            help="Must be globally unique across all GCP projects"
        )
        billing_account = st.text_input(
            "Billing Account", 
            placeholder="01783B-A7A65B-153181",
            help="Your GCP billing account ID"
        )
        organization_id = st.text_input(
            "Organization ID (Optional)", 
            placeholder="123456789012",
            help="If creating under an organization"
        )
    
    with col2:
        st.markdown("**Project Labels**")
        
        # Initialize labels in session state
        if 'project_labels' not in st.session_state:
            st.session_state.project_labels = {}
        
        # Display existing labels
        if st.session_state.project_labels:
            st.markdown("**Current Labels:**")
            for key, value in st.session_state.project_labels.items():
                col_key, col_value, col_del = st.columns([2, 2, 1])
                with col_key:
                    st.text(f"Key: {key}")
                with col_value:
                    st.text(f"Value: {value}")
                with col_del:
                    if st.button("🗑️", key=f"del_{key}"):
                        del st.session_state.project_labels[key]
                        st.rerun()
        
        # Add new label
        st.markdown("**Add New Label:**")
        col_key, col_value, col_add = st.columns([2, 2, 1])
        
        with col_key:
            new_label_key = st.text_input("Label Key", placeholder="environment", key="new_label_key")
        with col_value:
            new_label_value = st.text_input("Label Value", placeholder="production", key="new_label_value")
        with col_add:
            if st.button("➕ Add", key="add_label"):
                if new_label_key and new_label_value:
                    st.session_state.project_labels[new_label_key] = new_label_value
                    st.rerun()
                else:
                    st.warning("Please enter both key and value")
        
        # Clear all labels button
        if st.session_state.project_labels:
            if st.button("🗑️ Clear All Labels", key="clear_all_labels"):
                st.session_state.project_labels = {}
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
            "serviceusage.googleapis.com"
        ],
        "Networking": [
            "dns.googleapis.com",
            "vpcaccess.googleapis.com"
        ],
        "Serverless": [
            "run.googleapis.com",
            "cloudfunctions.googleapis.com"
        ],
        "Databases & Storage": [
            "sqladmin.googleapis.com",
            "bigquery.googleapis.com",
            "redis.googleapis.com"
        ],
        "Security & Secrets": [
            "secretmanager.googleapis.com"
        ],
        "Messaging & Events": [
            "pubsub.googleapis.com"
        ],
        "Containers & Artifacts": [
            "container.googleapis.com",
            "artifactregistry.googleapis.com"
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
    
    # VPC Configuration
    if st.checkbox("🌐 Create VPC Network"):
        st.markdown("**VPC Settings**")
        col1, col2 = st.columns(2)
        with col1:
            vpc_name = st.text_input("VPC Name", value="my-vpc", key="vpc_name")
        with col2:
            routing_mode = st.selectbox("Routing Mode", ["GLOBAL", "REGIONAL"], key="routing_mode")
        
        resources["vpc"] = {
            "name": vpc_name,
            "routing_mode": routing_mode,
            "description": "VPC created via GUI"
        }
    
    # Subnets
    if st.checkbox("📡 Create Subnets"):
        st.markdown("**Subnet Configuration**")
        if 'subnets' not in st.session_state:
            st.session_state.subnets = []
        
        # Display existing subnets
        if st.session_state.subnets:
            st.markdown("**Current Subnets:**")
            for i, subnet in enumerate(st.session_state.subnets):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.text(f"Name: {subnet['name']}")
                with col2:
                    st.text(f"Region: {subnet['region']}")
                with col3:
                    st.text(f"CIDR: {subnet['ip_cidr_range']}")
                with col4:
                    if st.button("🗑️", key=f"del_subnet_{i}"):
                        st.session_state.subnets.pop(i)
                        st.rerun()
        
        # Add new subnet
        st.markdown("**Add New Subnet:**")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            subnet_name = st.text_input("Subnet Name", value="subnet-1", key="new_subnet_name")
        with col2:
            subnet_region = st.selectbox("Region", ["us-central1", "us-west1", "europe-west1"], key="new_subnet_region")
        with col3:
            subnet_cidr = st.text_input("CIDR Range", value="10.0.0.0/24", key="new_subnet_cidr")
        with col4:
            if st.button("➕ Add", key="add_subnet"):
                if subnet_name and subnet_cidr:
                    new_subnet = {
                        "name": subnet_name,
                        "region": subnet_region,
                        "ip_cidr_range": subnet_cidr,
                        "network": "my-vpc",  # Default to main VPC
                        "private_ip_google_access": True
                    }
                    st.session_state.subnets.append(new_subnet)
                    st.rerun()
        
        if st.session_state.subnets:
            resources["subnets"] = st.session_state.subnets
    
    # Firewall Rules
    if st.checkbox("🔥 Create Firewall Rules"):
        st.markdown("**Firewall Configuration**")
        if 'firewall_rules' not in st.session_state:
            st.session_state.firewall_rules = []
        
        # Display existing rules
        if st.session_state.firewall_rules:
            st.markdown("**Current Firewall Rules:**")
            for i, rule in enumerate(st.session_state.firewall_rules):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.text(f"Name: {rule['name']}")
                with col2:
                    st.text(f"Direction: {rule['direction']}")
                with col3:
                    st.text(f"Protocol: {rule['protocol']}")
                with col4:
                    if st.button("🗑️", key=f"del_firewall_{i}"):
                        st.session_state.firewall_rules.pop(i)
                        st.rerun()
        
        # Add new rule
        st.markdown("**Add New Firewall Rule:**")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            fw_name = st.text_input("Rule Name", value="allow-ssh", key="new_fw_name")
        with col2:
            fw_direction = st.selectbox("Direction", ["INGRESS", "EGRESS"], key="new_fw_direction")
        with col3:
            fw_protocol = st.selectbox("Protocol", ["tcp", "udp", "icmp", "all"], key="new_fw_protocol")
        with col4:
            if st.button("➕ Add", key="add_firewall"):
                if fw_name:
                    new_rule = {
                        "name": fw_name,
                        "network": "my-vpc",
                        "direction": fw_direction,
                        "protocol": fw_protocol,
                        "source_ranges": ["0.0.0.0/0"],
                        "allows": [{"protocol": fw_protocol, "ports": ["22"]}]
                    }
                    st.session_state.firewall_rules.append(new_rule)
                    st.rerun()
        
        if st.session_state.firewall_rules:
            resources["firewall_rules"] = st.session_state.firewall_rules
    
    # Service Accounts
    if st.checkbox("👤 Create Service Accounts"):
        st.markdown("**Service Account Configuration**")
        if 'service_accounts' not in st.session_state:
            st.session_state.service_accounts = []
        
        # Display existing service accounts
        if st.session_state.service_accounts:
            st.markdown("**Current Service Accounts:**")
            for i, sa in enumerate(st.session_state.service_accounts):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(f"ID: {sa['account_id']}")
                with col2:
                    st.text(f"Name: {sa.get('display_name', 'N/A')}")
                with col3:
                    if st.button("🗑️", key=f"del_sa_{i}"):
                        st.session_state.service_accounts.pop(i)
                        st.rerun()
        
        # Add new service account
        st.markdown("**Add New Service Account:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sa_id = st.text_input("Account ID", value="my-service-account", key="new_sa_id")
        with col2:
            sa_display = st.text_input("Display Name", value="My Service Account", key="new_sa_display")
        with col3:
            if st.button("➕ Add", key="add_service_account"):
                if sa_id:
                    new_sa = {
                        "account_id": sa_id,
                        "display_name": sa_display,
                        "description": "Service account created via GUI"
                    }
                    st.session_state.service_accounts.append(new_sa)
                    st.rerun()
        
        if st.session_state.service_accounts:
            resources["service_accounts"] = st.session_state.service_accounts
    
    # IAM Bindings
    if st.checkbox("🔐 Create IAM Bindings"):
        st.markdown("**IAM Binding Configuration**")
        if 'iam_bindings' not in st.session_state:
            st.session_state.iam_bindings = []
        
        # Display existing bindings
        if st.session_state.iam_bindings:
            st.markdown("**Current IAM Bindings:**")
            for i, binding in enumerate(st.session_state.iam_bindings):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Role: {binding['role']}")
                with col2:
                    st.text(f"Member: {binding['member']}")
                with col3:
                    if st.button("🗑️", key=f"del_iam_{i}"):
                        st.session_state.iam_bindings.pop(i)
                        st.rerun()
        
        # Add new binding
        st.markdown("**Add New IAM Binding:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            iam_role = st.selectbox("Role", [
                "roles/storage.admin",
                "roles/compute.admin", 
                "roles/editor",
                "roles/viewer"
            ], key="new_iam_role")
        with col2:
            iam_member = st.text_input("Member", value="user:example@domain.com", key="new_iam_member")
        with col3:
            if st.button("➕ Add", key="add_iam_binding"):
                if iam_role and iam_member:
                    new_binding = {
                        "role": iam_role,
                        "member": iam_member
                    }
                    st.session_state.iam_bindings.append(new_binding)
                    st.rerun()
        
        if st.session_state.iam_bindings:
            resources["iam_bindings"] = st.session_state.iam_bindings
    
    # Compute Instances
    if st.checkbox("💻 Create Compute Instances"):
        st.markdown("**VM Configuration**")
        if 'compute_instances' not in st.session_state:
            st.session_state.compute_instances = []
        
        # Display existing instances
        if st.session_state.compute_instances:
            st.markdown("**Current Compute Instances:**")
            for i, vm in enumerate(st.session_state.compute_instances):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.text(f"Name: {vm['name']}")
                with col2:
                    st.text(f"Zone: {vm['zone']}")
                with col3:
                    st.text(f"Type: {vm['machine_type']}")
                with col4:
                    if st.button("🗑️", key=f"del_vm_{i}"):
                        st.session_state.compute_instances.pop(i)
                        st.rerun()
        
        # Add new instance
        st.markdown("**Add New Compute Instance:**")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            vm_name = st.text_input("VM Name", value="my-vm", key="new_vm_name")
        with col2:
            vm_zone = st.selectbox("Zone", ["us-central1-a", "us-west1-a", "europe-west1-a"], key="new_vm_zone")
        with col3:
            vm_type = st.selectbox("Machine Type", ["e2-micro", "e2-small", "e2-medium"], key="new_vm_type")
        with col4:
            if st.button("➕ Add", key="add_vm"):
                if vm_name:
                    new_vm = {
                        "name": vm_name,
                        "zone": vm_zone,
                        "machine_type": vm_type,
                        "image": "debian-cloud/debian-11",
                        "create_public_ip": False
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
        
        # Display existing buckets
        if st.session_state.storage_buckets:
            st.markdown("**Current Storage Buckets:**")
            for i, bucket in enumerate(st.session_state.storage_buckets):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {bucket['name']}")
                with col2:
                    st.text(f"Location: {bucket['location']}")
                with col3:
                    if st.button("🗑️", key=f"del_bucket_{i}"):
                        st.session_state.storage_buckets.pop(i)
                        st.rerun()
        
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
        
        # Display existing services
        if st.session_state.cloud_run_services:
            st.markdown("**Current Cloud Run Services:**")
            for i, service in enumerate(st.session_state.cloud_run_services):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Name: {service['name']}")
                with col2:
                    st.text(f"Location: {service['location']}")
                with col3:
                    if st.button("🗑️", key=f"del_cr_{i}"):
                        st.session_state.cloud_run_services.pop(i)
                        st.rerun()
        
        # Add new service
        st.markdown("**Add New Cloud Run Service:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            service_name = st.text_input("Service Name", value="my-service", key="new_cr_name")
        with col2:
            service_location = st.selectbox("Location", ["us-central1", "us-west1", "europe-west1"], key="new_cr_location")
        with col3:
            if st.button("➕ Add", key="add_cr_service"):
                if service_name:
                    new_service = {
                        "name": service_name,
                        "location": service_location,
                        "image": "gcr.io/cloudrun/hello",
                        "allow_unauthenticated": True
                    }
                    st.session_state.cloud_run_services.append(new_service)
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
    
    # Generate Configuration
    st.subheader("📄 Generated Configuration")
    
    if st.button("🔄 Generate YAML Configuration"):
        if not project_id or not billing_account:
            st.error("Please fill in Project ID and Billing Account")
            return
        
        config = {
            "project_id": project_id,
            "billing_account": billing_account,
            "organization_id": organization_id if organization_id else None,
            "labels": labels,
            "apis": selected_apis,
            "resources": resources
        }
        
        # Display the configuration
        st.code(yaml.dump(config, default_flow_style=False), language="yaml")
        
        # Save to session state
        st.session_state.generated_config = config
        st.session_state.config_filename = f"{project_id}.yaml"
        
        st.success(f"Configuration generated for project: {project_id}")
        
        # Download button
        yaml_content = yaml.dump(config, default_flow_style=False)
        st.download_button(
            label="📥 Download YAML Configuration",
            data=yaml_content,
            file_name=f"{project_id}.yaml",
            mime="text/yaml"
        )

def config_manager():
    st.header("📋 Configuration Manager")
    st.markdown("Manage and edit your project configurations")
    
    # List existing configs
    configs_dir = project_root / "configs"
    if configs_dir.exists():
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
        st.warning("Configs directory not found. Please ensure you're running from the project root.")
    
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
                height=400,
                language="yaml"
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

def deploy_config(config_file, plan_only=False, auto_approve=False):
    """Deploy a configuration using the existing deploy script"""
    st.subheader("🔄 Deployment Progress")
    
    # Show deployment info
    config_path = project_root / "configs" / config_file
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    st.info(f"Deploying project: **{config.get('project_id', 'Unknown')}**")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Run the deploy script
        status_text.text("Initializing deployment...")
        progress_bar.progress(10)
        
        cmd = [sys.executable, str(project_root / "scripts" / "deploy.py"), str(config_path)]
        
        if plan_only:
            cmd.append("--plan-only")
        if auto_approve:
            cmd.append("--auto-approve")
        
        status_text.text("Running deployment script...")
        progress_bar.progress(30)
        
        # Execute the command
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        progress_bar.progress(80)
        status_text.text("Processing results...")
        
        # Display results
        if result.returncode == 0:
            st.success("✅ Deployment completed successfully!")
            progress_bar.progress(100)
            
            if result.stdout:
                st.subheader("📋 Deployment Output")
                st.code(result.stdout)
        else:
            st.error("❌ Deployment failed!")
            progress_bar.progress(100)
            
            if result.stderr:
                st.subheader("🚨 Error Details")
                st.code(result.stderr)
            
            if result.stdout:
                st.subheader("📋 Output")
                st.code(result.stdout)
        
        status_text.text("Deployment completed")
        
    except subprocess.TimeoutExpired:
        st.error("⏰ Deployment timed out after 5 minutes")
        progress_bar.progress(100)
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
    st.markdown("**Advanced Project with VPC, Cloud Run, and Database**")
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
            "cloud_sql_instances": [{
                "name": "app-database",
                "database_version": "POSTGRES_14",
                "region": "us-central1",
                "tier": "db-f1-micro"
            }]
        }
    }
    
    st.code(yaml.dump(advanced_example, default_flow_style=False), language="yaml")
    
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
