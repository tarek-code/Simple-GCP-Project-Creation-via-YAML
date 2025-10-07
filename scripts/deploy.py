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

def write_minimal_root_tf(run_dir: str, module_source_rel: str, include_project_module: bool, create_project: bool) -> None:
    """Create minimal Terraform root files in run_dir. Optionally include the project module."""
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
    )
    if include_project_module:
        required += (
            f"module \"project\" {{\n"
            f"  source          = \"{module_source_rel}\"\n"
            f"  project_id      = var.project_id\n"
            f"  organization_id = var.organization_id\n"
            f"  billing_account = var.billing_account\n"
            f"  labels          = var.labels\n"
            f"  apis            = var.apis\n"
            f"  create_project  = {str(create_project).lower()}\n"
            f"}}\n"
        )
    else:
        # If project exists, still allow API enablement without module
        required += (
            "resource \"google_project_service\" \"enabled_apis\" {\n"
            "  for_each = toset(var.apis)\n"
            "  project  = var.project_id\n"
            "  service  = each.value\n"
            "}\n"
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
    # Track modules created to wire dependencies
    subnet_name_to_module: dict = {}
    vpc_connector_name_to_module: dict = {}

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
                f"  force_destroy = {str(b.get('force_destroy', False)).lower()}",
                f"  storage_class = {json.dumps(b.get('storage_class'))}",
                f"  public_access_prevention = {json.dumps(b.get('public_access_prevention'))}",
                f"  default_kms_key_name = {json.dumps(b.get('default_kms_key_name'))}",
                f"  logging = {json.dumps(b.get('logging'))}",
                f"  cors = {json.dumps(b.get('cors', []))}",
                f"  lifecycle_rules = {json.dumps(b.get('lifecycle_rules', []))}",
                f"  retention_policy = {json.dumps(b.get('retention_policy'))}",
                f"  labels = {json.dumps(b.get('labels', {}))}",
                f"}}\n",
            ])
        )

    # VPC (support single object or list under 'vpc' or 'vpcs')
    vpc_items: List[dict] = []
    if "vpc" in resources:
        if isinstance(resources["vpc"], list):
            vpc_items.extend([v for v in resources["vpc"] if isinstance(v, dict)])
        elif isinstance(resources["vpc"], dict):
            vpc_items.append(resources["vpc"]) 
    if isinstance(resources.get("vpcs"), list):
        vpc_items.extend([v for v in resources["vpcs"] if isinstance(v, dict)])

    for i, vpc in enumerate(vpc_items, start=1):
        module_name = "vpc" if i == 1 else f"vpc_{i}"
        blocks.append(
            "\n".join([
                f"module \"{module_name}\" {{",
                f"  source  = \"{mod_source('vpc')}\"",
                f"  project_id   = var.project_id",
                f"  name         = \"{vpc['name']}\"",
                f"  routing_mode = \"{vpc.get('routing_mode', 'GLOBAL')}\"",
                f"  description  = {json.dumps(vpc.get('description'))}",
                f"  mtu          = {json.dumps(vpc.get('mtu'))}",
                f"  auto_create_subnetworks = {str(vpc.get('auto_create_subnetworks', False)).lower()}",
                f"  bgp_best_path_selection_mode = {json.dumps(vpc.get('bgp_best_path_selection_mode'))}",
                f"  bgp_always_compare_med = {json.dumps(vpc.get('bgp_always_compare_med'))}",
                f"  bgp_inter_region_cost = {json.dumps(vpc.get('bgp_inter_region_cost'))}",
                f"  enable_ula_internal_ipv6 = {str(vpc.get('enable_ula_internal_ipv6', False)).lower()}",
                f"  internal_ipv6_range = {json.dumps(vpc.get('internal_ipv6_range'))}",
                f"  network_firewall_policy_enforcement_order = {json.dumps(vpc.get('network_firewall_policy_enforcement_order'))}",
                f"  network_profile = {json.dumps(vpc.get('network_profile'))}",
                f"  delete_default_routes_on_create = {str(vpc.get('delete_default_routes_on_create', False)).lower()}",
                f"  resource_manager_tags = {json.dumps(vpc.get('resource_manager_tags', {}))}",
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
                f"  secondary_ip_ranges = {json.dumps(sn.get('secondary_ip_ranges', []))}",
                f"}}\n",
            ])
        )
        # map subnet name -> module address
        subnet_name_to_module[sn['name']] = f"module.subnet_{i}"

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
                f"  source_tags = {json.dumps(fw.get('source_tags', []))}",
                f"  source_service_accounts = {json.dumps(fw.get('source_service_accounts', []))}",
                f"  target_tags   = {json.dumps(fw.get('target_tags', []))}",
                f"  target_service_accounts = {json.dumps(fw.get('target_service_accounts', []))}",
                f"  destination_ranges      = {json.dumps(fw.get('destination_ranges', []))}",
                f"  disabled = {str(fw.get('disabled', False)).lower()}",
                f"  description = {json.dumps(fw.get('description'))}",
                f"  enable_logging = {str(fw.get('enable_logging', False)).lower()}",
                f"  log_config = {json.dumps(fw.get('log_config'))}",
                f"  allows = {json.dumps(fw.get('allows', []))}",
                f"  denies = {json.dumps(fw.get('denies', []))}",
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
                f"  member  = {json.dumps(ib.get('member'))}",
                f"  members = {json.dumps(ib.get('members', []))}",
                f"  condition = {json.dumps(ib.get('condition'))}",
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
                f"  subscriptions = {json.dumps(pt.get('subscriptions', []))}",
                f"}}\n",
            ])
        )

    # Cloud Run
    for i, cr in enumerate(resources.get("cloud_run_services", []) or [], start=1):
        lines = [
            f"module \"cloud_run_{i}\" {{",
            f"  source   = \"{mod_source('cloud_run')}\"",
            f"  project_id = var.project_id",
            f"  name     = \"{cr['name']}\"",
            f"  location = \"{cr.get('location', 'us-central1')}\"",
            f"  image    = \"{cr['image']}\"",
        ]
        if 'allow_unauthenticated' in cr:
            lines.append(f"  allow_unauthenticated = {str(bool(cr['allow_unauthenticated'])).lower()}")
        if 'vpc_connector' in cr and cr['vpc_connector']:
            lines.append(f"  vpc_connector = \"{cr['vpc_connector']}\"")
        if 'egress' in cr and cr['egress']:
            lines.append(f"  egress = \"{cr['egress']}\"")
        # depends_on wiring to ensure connector exists before Cloud Run
        dep = None
        vc_name = cr.get('vpc_connector')
        if vc_name:
            # capture module name if it will be created below
            # will add after connector loop
            dep = vc_name
        lines.append("}\n")
        blocks.append("\n".join(lines))

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
                f"  deletion_protection = {str(cs.get('deletion_protection', False)).lower()}",
                f"  availability_type = {json.dumps(cs.get('availability_type'))}",
                f"  disk_size = {json.dumps(cs.get('disk_size'))}",
                f"  disk_type = {json.dumps(cs.get('disk_type'))}",
                f"  ipv4_enabled = {str(cs.get('ipv4_enabled', False)).lower()}",
                f"  private_network = {json.dumps(cs.get('private_network'))}",
                f"  authorized_networks = {json.dumps(cs.get('authorized_networks', []))}",
                f"  backup_configuration = {json.dumps(cs.get('backup_configuration'))}",
                f"  maintenance_window = {json.dumps(cs.get('maintenance_window'))}",
                f"  database_flags = {json.dumps(cs.get('database_flags', []))}",
                f"  insights_config = {json.dumps(cs.get('insights_config'))}",
                f"  kms_key_name = {json.dumps(cs.get('kms_key_name'))}",
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
                f"  replication = {json.dumps(sm.get('replication'))}",
                f"  additional_versions = {json.dumps(sm.get('additional_versions', []))}",
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
                f"  record_sets = {json.dumps(dz.get('record_sets', []))}",
                f"}}\n",
            ])
        )

    # Static IPs (global/regional)
    for i, ip in enumerate(resources.get("static_ips", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"static_ip_{i}\" {{",
                f"  source   = \"{mod_source('static_ip')}\"",
                f"  project_id  = var.project_id",
                f"  name        = \"{ip['name']}\"",
                f"  address_type = {json.dumps(ip.get('address_type', 'EXTERNAL'))}",
                f"  region       = {json.dumps(ip.get('region'))}",
                f"  network_tier = {json.dumps(ip.get('network_tier'))}",
                f"  subnetwork   = {json.dumps(ip.get('subnetwork'))}",
                f"  purpose      = {json.dumps(ip.get('purpose'))}",
                f"  address      = {json.dumps(ip.get('address'))}",
                f"  description  = {json.dumps(ip.get('description'))}",
                f"}}\n",
            ])
        )

    # Compute instances (VMs)
    for i, vm in enumerate(resources.get("compute_instances", []) or [], start=1):
        depends_lines: List[str] = []
        vm_subnet = vm.get('subnetwork')
        if isinstance(vm_subnet, str) and vm_subnet in subnet_name_to_module:
            # ensure VM waits for the subnet module
            depends_lines.append(f"  depends_on = [ {subnet_name_to_module[vm_subnet]} ]")

        block_lines = [
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
        ]
        block_lines.extend(depends_lines)
        block_lines.append("}\n")
        blocks.append("\n".join(block_lines))

    # Standalone persistent disks
    for i, dk in enumerate(resources.get("disks", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"disk_{i}\" {{",
                f"  source   = \"{mod_source('compute_disk')}\"",
                f"  project_id = var.project_id",
                f"  name     = \"{dk['name']}\"",
                f"  zone     = \"{dk.get('zone', 'us-central1-a')}\"",
                f"  size_gb  = {int(dk.get('size_gb', 10))}",
                f"  type     = {json.dumps(dk.get('type', 'pd-standard'))}",
                f"  image    = {json.dumps(dk.get('image'))}",
                f"  snapshot = {json.dumps(dk.get('snapshot'))}",
                f"  labels   = {json.dumps(dk.get('labels', {}))}",
                f"  kms_key_self_link = {json.dumps(dk.get('kms_key_self_link'))}",
                f"}}\n",
            ])
        )

    # BigQuery datasets
    for i, ds in enumerate(resources.get("bigquery_datasets", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"bigquery_dataset_{i}\" {{",
                f"  source    = \"{mod_source('bigquery_dataset')}\"",
                f"  project_id = var.project_id",
                f"  dataset_id = \"{ds['dataset_id']}\"",
                f"  location   = \"{ds.get('location', 'US')}\"",
                f"  labels     = {json.dumps(ds.get('labels', {}))}",
                f"}}\n",
            ])
        )

    # Cloud Functions (Gen2)
    for i, fn in enumerate(resources.get("cloud_functions", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"cloud_function_{i}\" {{",
                f"  source       = \"{mod_source('cloud_functions')}\"",
                f"  project_id   = var.project_id",
                f"  name         = \"{fn['name']}\"",
                f"  location     = \"{fn.get('location', 'us-central1')}\"",
                f"  description  = {json.dumps(fn.get('description'))}",
                f"  runtime      = \"{fn['runtime']}\"",
                f"  entry_point  = \"{fn['entry_point']}\"",
                f"  source_bucket = \"{fn['source_bucket']}\"",
                f"  source_object = \"{fn['source_object']}\"",
                f"  memory       = \"{fn.get('memory', '256M')}\"",
                f"  timeout_seconds = {int(fn.get('timeout_seconds', 60))}",
                f"  ingress_settings = \"{fn.get('ingress_settings', 'ALLOW_ALL')}\"",
                f"  max_instance_count = {int(fn.get('max_instance_count', 1))}",
                f"}}\n",
            ])
        )

    # GKE
    if gke := resources.get("gke"):
        blocks.append(
            "\n".join([
                f"module \"gke\" {{",
                f"  source        = \"{mod_source('gke')}\"",
                f"  project_id    = var.project_id",
                f"  name          = \"{gke['name']}\"",
                f"  location      = \"{gke.get('location', 'us-central1')}\"",
                f"  node_pool_name = \"{gke.get('node_pool_name', 'default-pool')}\"",
                f"  node_count    = {int(gke.get('node_count', 1))}",
                f"  machine_type  = \"{gke.get('machine_type', 'e2-standard-2')}\"",
                f"  labels        = {json.dumps(gke.get('labels', {}))}",
                f"  tags          = {json.dumps(gke.get('tags', []))}",
                f"  network       = {json.dumps(gke.get('network'))}",
                f"  subnetwork    = {json.dumps(gke.get('subnetwork'))}",
                f"  cluster_secondary_range_name  = {json.dumps(gke.get('cluster_secondary_range_name'))}",
                f"  services_secondary_range_name = {json.dumps(gke.get('services_secondary_range_name'))}",
                f"  enable_private_nodes = {str(gke.get('enable_private_nodes', False)).lower()}",
                f"  master_ipv4_cidr_block = {json.dumps(gke.get('master_ipv4_cidr_block'))}",
                f"  enable_network_policy = {str(gke.get('enable_network_policy', False)).lower()}",
                f"  node_auto_scaling = {json.dumps(gke.get('node_auto_scaling'))}",
                f"  node_labels = {json.dumps(gke.get('node_labels', {}))}",
                f"  node_taints = {json.dumps(gke.get('node_taints', []))}",
                f"}}\n",
            ])
        )

    # Cloud Router
    if cr := resources.get("cloud_router"):
        blocks.append(
            "\n".join([
                f"module \"cloud_router\" {{",
                f"  source    = \"{mod_source('cloud_router')}\"",
                f"  project_id = var.project_id",
                f"  name      = \"{cr['name']}\"",
                f"  region    = \"{cr['region']}\"",
                f"  network   = \"{cr['network']}\"",
                f"  asn       = {json.dumps(cr.get('asn'))}",
                f"  bgp_advertised_ip_ranges = {json.dumps(cr.get('bgp_advertised_ip_ranges', []))}",
                f"  interfaces = {json.dumps(cr.get('interfaces', []))}",
                f"  bgp_peers  = {json.dumps(cr.get('bgp_peers', []))}",
                f"}}\n",
            ])
        )

    # Cloud NAT
    if nat := resources.get("cloud_nat"):
        blocks.append(
            "\n".join([
                f"module \"cloud_nat\" {{",
                f"  source    = \"{mod_source('cloud_nat')}\"",
                f"  project_id = var.project_id",
                f"  name      = \"{nat['name']}\"",
                f"  region    = \"{nat['region']}\"",
                f"  router    = \"{nat['router']}\"",
                f"  nat_ip_allocation = \"{nat.get('nat_ip_allocation', 'AUTO_ONLY')}\"",
                f"  source_subnetwork_ip_ranges_to_nat = \"{nat.get('source_subnetwork_ip_ranges_to_nat', 'ALL_SUBNETWORKS_ALL_IP_RANGES')}\"",
                f"}}\n",
            ])
        )

    # Memorystore Redis
    for i, r in enumerate(resources.get("redis_instances", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"redis_{i}\" {{",
                f"  source    = \"{mod_source('memorystore_redis')}\"",
                f"  project_id = var.project_id",
                f"  name       = \"{r['name']}\"",
                f"  region     = \"{r.get('region', 'us-central1')}\"",
                f"  tier       = \"{r.get('tier', 'BASIC')}\"",
                f"  memory_size_gb = {int(r.get('memory_size_gb', 1))}",
                f"  redis_version  = \"{r.get('redis_version', 'REDIS_6_X')}\"",
                f"  display_name   = {json.dumps(r.get('display_name'))}",
                f"  connect_mode   = \"{r.get('connect_mode', 'DIRECT_PEERING')}\"",
                f"  authorized_network = {json.dumps(r.get('authorized_network'))}",
                f"  maintenance_policy = {json.dumps(r.get('maintenance_policy'))}",
                f"  persistence_config = {json.dumps(r.get('persistence_config'))}",
                f"  labels = {json.dumps(r.get('labels', {}))}",
                f"}}\n",
            ])
        )

    # Serverless VPC connectors
    for i, c in enumerate(resources.get("serverless_vpc_connectors", []) or [], start=1):
        blocks.append(
            "\n".join([
                f"module \"serverless_vpc_connector_{i}\" {{",
                f"  source    = \"{mod_source('serverless_vpc_connector')}\"",
                f"  project_id = var.project_id",
                f"  name       = \"{c['name']}\"",
                f"  region     = \"{c['region']}\"",
                f"  network    = \"{c['network']}\"",
                f"  ip_cidr_range = \"{c['ip_cidr_range']}\"",
                f"}}\n",
            ])
        )
        vpc_connector_name_to_module[c['name']] = f"module.serverless_vpc_connector_{i}"

    # After defining connectors, append depends_on to Cloud Run blocks that reference one
    if resources.get("cloud_run_services"):
        updated_blocks: List[str] = []
        for block in blocks:
            if block.startswith("module \"cloud_run_") and "vpc_connector = \"" in block:
                # extract connector name
                import re
                m = re.search(r"vpc_connector = \"([^\"]+)\"", block)
                if m:
                    name = m.group(1)
                    if name in vpc_connector_name_to_module:
                        # inject depends_on before closing brace
                        block = block.replace("}\n", f"  depends_on = [ {vpc_connector_name_to_module[name]} ]\n}}\n")
            updated_blocks.append(block)
        blocks = updated_blocks

    return "\n".join(blocks)

def run_terraform_in_dir(run_dir: str, tfvars_path: str, project_id: str, has_project_module: bool) -> None:
    cwd_before = os.getcwd()
    try:
        os.chdir(run_dir)
        print(f"[INFO] Running Terraform in: {run_dir}")
        subprocess.run(["terraform", "init"], check=True)
        # Phase 1: plan project/APIs if module present
        if has_project_module:
            print("[INFO] Phase 1: Plan project and APIs (-target=module.project)")
            subprocess.run([
                "terraform", "plan",
                "-target=module.project",
                "-var-file", tfvars_path,
            ], check=True)
        else:
            print("[INFO] Phase 1: Project exists; skipping targeted plan.")
        # Phase 2: full plan for remaining resources
        print("[INFO] Phase 2: Full plan for remaining resources")
        subprocess.run([
            "terraform", "plan",
            "-var-file", tfvars_path,
        ], check=True)

        # Ask whether to apply for this project
        # Skip prompt if SKIP_APPLY_PROMPT environment variable is set
        if os.environ.get("SKIP_APPLY_PROMPT"):
            auto_answer = os.environ.get("AUTO_APPROVE_ANSWER", "no")
            print(f"[INFO] Skipping apply prompt (SKIP_APPLY_PROMPT=true); auto-answering '{auto_answer}'.")
            answer = auto_answer
        else:
            answer = input(f"Apply changes for project '{project_id}'? (yes/no): ")
        
        if answer.strip().lower() in ("yes", "y"):
            print("[INFO] Proceeding to apply...")
            # Phase 1 apply: project and APIs (only if module present)
            if has_project_module:
                try:
                    subprocess.run([
                        "terraform", "apply",
                        "-target=module.project",
                        "-var-file", tfvars_path,
                        "-auto-approve",
                    ], check=True)
                except subprocess.CalledProcessError as e:
                    print("[WARN] Targeted apply for project module failed (likely exists). Switching to existing-project mode and continuing.")
                    # Rewrite module block to force create_project=false, then re-plan
                    try:
                        main_tf_path = os.path.join(run_dir, "main.tf")
                        with open(main_tf_path, "r", encoding="utf-8") as mf:
                            content = mf.read()
                        if "create_project" in content:
                            content = content.replace("create_project  = true", "create_project  = false")
                        else:
                            content = content.replace("apis            = var.apis\n}", "apis            = var.apis\n  create_project  = false\n}")
                        with open(main_tf_path, "w", encoding="utf-8") as mf:
                            mf.write(content)
                        # Re-plan after switching mode
                        subprocess.run(["terraform", "plan", "-var-file", tfvars_path], check=True)
                    except Exception as ee:
                        print(f"[WARN] Could not rewrite main.tf to disable project creation: {ee}")
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

        # Detect if project exists to decide whether to include project module
        module_source_rel = rel(run_dir, os.path.join(project_root, "modules", "project"))
        project_exists = False
        try:
            result = subprocess.run([
                "gcloud", "projects", "list",
                f"--filter=projectId={project_id}",
                "--format=value(projectId)"
            ], check=True, capture_output=True, text=True)
            if result.stdout.strip() == project_id:
                project_exists = True
                print(f"[INFO] Project '{project_id}' already exists; will not include project module.")
            else:
                print(f"[INFO] Project '{project_id}' not found in gcloud list; will include project module to create it.")
        except Exception as e:
            print(f"[WARN] Could not determine project existence via gcloud ({e}); assuming not exists.")

        write_minimal_root_tf(run_dir, module_source_rel, include_project_module=not project_exists, create_project=not project_exists)

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
        run_terraform_in_dir(run_dir, tfvars_path, project_id, has_project_module=not project_exists)

if __name__ == "__main__":
    main()
