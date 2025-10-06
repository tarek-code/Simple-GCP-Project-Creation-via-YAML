import streamlit as st
import yaml
import json
import subprocess
import os
import sys
from pathlib import Path

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

def main():
    st.title("☁️ GCP Project Creator")
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
    
    # VPC Configuration (multiple)
    if st.checkbox("🌐 Create VPC Networks"):
        st.markdown("**VPC Settings**")
        if 'vpcs' not in st.session_state:
            st.session_state.vpcs = []
        
        # Existing VPCs with inline editing
        if st.session_state.vpcs:
            st.markdown("**Current VPCs:**")
            for i, v in enumerate(list(st.session_state.vpcs)):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    new_name = st.text_input("Name", value=v['name'], key=f"vpc_name_{i}")
                with col2:
                    new_routing = st.selectbox("Routing", ["GLOBAL", "REGIONAL"], 
                                             index=0 if v.get('routing_mode', 'GLOBAL') == 'GLOBAL' else 1,
                                             key=f"vpc_routing_{i}")
                with col3:
                    if st.button("🗑️", key=f"del_vpc_{i}"):
                        st.session_state.vpcs.pop(i)
                        st.rerun()
                
                # Update if changed
                if new_name != v['name'] or new_routing != v.get('routing_mode', 'GLOBAL'):
                    st.session_state.vpcs[i]['name'] = new_name
                    st.session_state.vpcs[i]['routing_mode'] = new_routing
        
        # Add VPC
        st.markdown("**Add New VPC:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_vpc_name = st.text_input("VPC Name", value="my-vpc", key="new_vpc_name")
        with col2:
            new_vpc_routing = st.selectbox("Routing Mode", ["GLOBAL", "REGIONAL"], key="new_vpc_routing")
        with col3:
            if st.button("➕ Add", key="add_vpc"):
                if new_vpc_name:
                    st.session_state.vpcs.append({
                        "name": new_vpc_name,
                        "routing_mode": new_vpc_routing,
                        "description": "VPC created via GUI"
                    })
                    st.rerun()
        
        if st.session_state.vpcs:
            # Prefer list under 'vpcs' to support multiple
            resources["vpcs"] = st.session_state.vpcs
    
    # Subnets
    if st.checkbox("📡 Create Subnets"):
        st.markdown("**Subnet Configuration**")
        if 'subnets' not in st.session_state:
            st.session_state.subnets = []
        
        # Display existing subnets with inline editing
        if st.session_state.subnets:
            st.markdown("**Current Subnets:**")
            for i, subnet in enumerate(list(st.session_state.subnets)):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    new_name = st.text_input("Name", value=subnet['name'], key=f"subnet_name_{i}")
                with col2:
                    new_region = st.selectbox("Region", ["us-central1", "us-west1", "europe-west1"], 
                                            index=["us-central1", "us-west1", "europe-west1"].index(subnet['region']),
                                            key=f"subnet_region_{i}")
                with col3:
                    new_cidr = st.text_input("CIDR", value=subnet['ip_cidr_range'], key=f"subnet_cidr_{i}")
                with col4:
                    if st.button("🗑️", key=f"del_subnet_{i}"):
                        st.session_state.subnets.pop(i)
                        st.rerun()
                
                # Update if changed
                if (new_name != subnet['name'] or new_region != subnet['region'] or 
                    new_cidr != subnet['ip_cidr_range']):
                    st.session_state.subnets[i]['name'] = new_name
                    st.session_state.subnets[i]['region'] = new_region
                    st.session_state.subnets[i]['ip_cidr_range'] = new_cidr
        
        # Add new subnet
        st.markdown("**Add New Subnet:**")
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            subnet_name = st.text_input("Subnet Name", value="subnet-1", key="new_subnet_name")
        with col2:
            subnet_region = st.selectbox("Region", ["us-central1", "us-west1", "europe-west1"], key="new_subnet_region")
        with col3:
            subnet_cidr = st.text_input("CIDR Range", value="10.0.0.0/24", key="new_subnet_cidr")

        # Network selection (which VPC?)
        # If a VPC was defined above in this form, offer it; otherwise allow manual entry
        vpc_options = []
        # Collect VPCs defined in this form run
        if resources.get("vpc") and resources["vpc"].get("name"):
            vpc_options.append(resources["vpc"]["name"])
        if "vpcs" in resources:
            for v in resources["vpcs"]:
                if isinstance(v, dict) and v.get("name"):
                    vpc_options.append(v["name"])
        st.markdown("**Attach to VPC**")
        if vpc_options:
            subnet_network = st.selectbox("VPC Network", vpc_options, key="new_subnet_network_select")
        else:
            subnet_network = st.text_input("VPC Network Name", value="", placeholder="enter existing VPC name", key="new_subnet_network_text")

        if st.button("➕ Add", key="add_subnet"):
            if subnet_name and subnet_cidr and (subnet_network or (vpc_options and subnet_network)):
                new_subnet = {
                    "name": subnet_name,
                    "region": subnet_region,
                    "ip_cidr_range": subnet_cidr,
                    "network": subnet_network,
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
        
        # Display existing rules with inline editing
        if st.session_state.firewall_rules:
            st.markdown("**Current Firewall Rules:**")
            for i, rule in enumerate(list(st.session_state.firewall_rules)):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    new_name = st.text_input("Name", value=rule['name'], key=f"fw_name_{i}")
                with col2:
                    new_direction = st.selectbox("Direction", ["INGRESS", "EGRESS"], 
                                               index=0 if rule['direction'] == 'INGRESS' else 1,
                                               key=f"fw_direction_{i}")
                with col3:
                    new_protocol = st.selectbox("Protocol", ["tcp", "udp", "icmp", "all"], 
                                              index=["tcp", "udp", "icmp", "all"].index(rule['protocol']),
                                              key=f"fw_protocol_{i}")
                with col4:
                    if st.button("🗑️", key=f"del_firewall_{i}"):
                        st.session_state.firewall_rules.pop(i)
                        st.rerun()
                
                # Update if changed
                if (new_name != rule['name'] or new_direction != rule['direction'] or 
                    new_protocol != rule['protocol']):
                    st.session_state.firewall_rules[i]['name'] = new_name
                    st.session_state.firewall_rules[i]['direction'] = new_direction
                    st.session_state.firewall_rules[i]['protocol'] = new_protocol
        
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
        
        # Display existing service accounts with inline editing
        if st.session_state.service_accounts:
            st.markdown("**Current Service Accounts:**")
            for i, sa in enumerate(list(st.session_state.service_accounts)):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    new_id = st.text_input("Account ID", value=sa['account_id'], key=f"sa_id_{i}")
                with col2:
                    new_display = st.text_input("Display Name", value=sa.get('display_name', ''), key=f"sa_display_{i}")
                with col3:
                    if st.button("🗑️", key=f"del_sa_{i}"):
                        st.session_state.service_accounts.pop(i)
                        st.rerun()
                
                # Update if changed
                if new_id != sa['account_id'] or new_display != sa.get('display_name', ''):
                    st.session_state.service_accounts[i]['account_id'] = new_id
                    st.session_state.service_accounts[i]['display_name'] = new_display
        
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
        
        # Display existing bindings with inline editing
        if st.session_state.iam_bindings:
            st.markdown("**Current IAM Bindings:**")
            for i, binding in enumerate(list(st.session_state.iam_bindings)):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    new_role = st.selectbox("Role", [
                        "roles/storage.admin",
                        "roles/compute.admin", 
                        "roles/editor",
                        "roles/viewer"
                    ], index=[
                        "roles/storage.admin",
                        "roles/compute.admin", 
                        "roles/editor",
                        "roles/viewer"
                    ].index(binding['role']), key=f"iam_role_{i}")
                with col2:
                    new_member = st.text_input("Member", value=binding['member'], key=f"iam_member_{i}")
                with col3:
                    if st.button("🗑️", key=f"del_iam_{i}"):
                        st.session_state.iam_bindings.pop(i)
                        st.rerun()
                
                # Update if changed
                if new_role != binding['role'] or new_member != binding['member']:
                    st.session_state.iam_bindings[i]['role'] = new_role
                    st.session_state.iam_bindings[i]['member'] = new_member
        
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
        
        # Display existing instances with inline editing
        if st.session_state.compute_instances:
            st.markdown("**Current Compute Instances:**")
            for i, vm in enumerate(list(st.session_state.compute_instances)):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    new_name = st.text_input("Name", value=vm['name'], key=f"vm_name_{i}")
                with col2:
                    new_zone = st.selectbox("Zone", ["us-central1-a", "us-west1-a", "europe-west1-a"], 
                                          index=["us-central1-a", "us-west1-a", "europe-west1-a"].index(vm['zone']),
                                          key=f"vm_zone_{i}")
                with col3:
                    new_type = st.selectbox("Type", ["e2-micro", "e2-small", "e2-medium"], 
                                          index=["e2-micro", "e2-small", "e2-medium"].index(vm['machine_type']),
                                          key=f"vm_type_{i}")
                with col4:
                    if st.button("🗑️", key=f"del_vm_{i}"):
                        st.session_state.compute_instances.pop(i)
                        st.rerun()
                
                # Update if changed
                if (new_name != vm['name'] or new_zone != vm['zone'] or 
                    new_type != vm['machine_type']):
                    st.session_state.compute_instances[i]['name'] = new_name
                    st.session_state.compute_instances[i]['zone'] = new_zone
                    st.session_state.compute_instances[i]['machine_type'] = new_type
        
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
    
    # Generate Configuration
    st.subheader("📄 Generated Configuration")
    
    if st.button("🔄 Generate YAML Configuration"):
        if not project_id or not billing_account:
            st.error("Please fill in Project ID and Billing Account")
            return
        
        from collections import OrderedDict
        
        # Create ordered dictionary with specific order
        config = OrderedDict()
        config["project_id"] = project_id
        config["billing_account"] = billing_account
        config["labels"] = labels
        config["apis"] = selected_apis
        if organization_id:
            config["organization_id"] = organization_id
        config["resources"] = resources
        
        # Display the configuration
        st.code(yaml.dump(dict(config), default_flow_style=False, sort_keys=False), language="yaml")
        
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
        
        # Only check GCP auth if we're actually deploying (not planning)
        if not plan_only:
            # Check if gcloud is available and authenticated
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
                    else:
                        st.error("❌ Not authenticated with GCP. Run: `gcloud auth login`")
                else:
                    st.error("❌ gcloud command not found")
            except Exception as e:
                st.error(f"❌ Error checking gcloud: {str(e)}")
        else:
            st.info("ℹ️ Plan-only mode: No GCP authentication required")
        
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
