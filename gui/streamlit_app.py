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
        
        # Always include project_id and billing_account
        filtered_config["project_id"] = config["project_id"]
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
