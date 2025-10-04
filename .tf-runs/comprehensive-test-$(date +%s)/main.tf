terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.4.0"
    }
  }
}

provider "google" {
  project = var.project_id
}

module "project" {
  source          = "../../modules/project"
  project_id      = var.project_id
  organization_id = var.organization_id
  billing_account = var.billing_account
  labels          = var.labels
  apis            = var.apis
  create_project  = true
}


# Additional resources from YAML
module "storage_bucket_1" {
  source  = "../../modules/storage_bucket"
  project_id = var.project_id
  name        = "test-bucket-1"
  location    = "US"
  uniform_bucket_level_access = true
  enable_versioning = true
  force_destroy = false
  storage_class = null
  public_access_prevention = null
  default_kms_key_name = null
  logging = null
  cors = [{"origin": ["*"], "method": ["GET", "POST"], "response_header": ["*"], "max_age_seconds": 3600}]
  lifecycle_rules = [{"action": {"type": "Delete"}, "condition": {"age": 30}}]
  retention_policy = null
  labels = {"purpose": "test", "type": "general"}
}

module "storage_bucket_2" {
  source  = "../../modules/storage_bucket"
  project_id = var.project_id
  name        = "test-bucket-2"
  location    = "us-central1"
  uniform_bucket_level_access = false
  enable_versioning = false
  force_destroy = true
  storage_class = null
  public_access_prevention = null
  default_kms_key_name = null
  logging = null
  cors = []
  lifecycle_rules = []
  retention_policy = null
  labels = {"purpose": "test", "type": "regional"}
}

module "vpc" {
  source  = "../../modules/vpc"
  project_id   = var.project_id
  name         = "test-vpc"
  routing_mode = "GLOBAL"
  description  = "Comprehensive test VPC"
}

module "subnet_1" {
  source  = "../../modules/subnet"
  project_id     = var.project_id
  name           = "test-subnet-1"
  region         = "us-central1"
  ip_cidr_range  = "10.10.0.0/24"
  network        = "test-vpc"
  private_ip_google_access = true
  purpose        = null
  secondary_ip_ranges = [{"range_name": "pods", "ip_cidr_range": "10.20.0.0/16"}, {"range_name": "services", "ip_cidr_range": "10.30.0.0/16"}]
}

module "subnet_2" {
  source  = "../../modules/subnet"
  project_id     = var.project_id
  name           = "test-subnet-2"
  region         = "us-west1"
  ip_cidr_range  = "10.11.0.0/24"
  network        = "test-vpc"
  private_ip_google_access = false
  purpose        = null
  secondary_ip_ranges = []
}

module "firewall_1" {
  source  = "../../modules/firewall"
  project_id = var.project_id
  name       = "test-allow-ssh"
  network    = "test-vpc"
  direction  = "INGRESS"
  priority   = 1000
  protocol   = "tcp"
  ports      = ["22"]
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ssh"]
  target_service_accounts = []
  destination_ranges      = []
  allows = []
  denies = []
}

module "firewall_2" {
  source  = "../../modules/firewall"
  project_id = var.project_id
  name       = "test-allow-http"
  network    = "test-vpc"
  direction  = "INGRESS"
  priority   = 1000
  protocol   = "tcp"
  ports      = ["22"]
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web"]
  target_service_accounts = []
  destination_ranges      = []
  allows = []
  denies = []
}

module "firewall_3" {
  source  = "../../modules/firewall"
  project_id = var.project_id
  name       = "test-allow-internal"
  network    = "test-vpc"
  direction  = "INGRESS"
  priority   = 1000
  protocol   = "tcp"
  ports      = ["22"]
  source_ranges = ["0.0.0.0/0"]
  target_tags   = []
  target_service_accounts = []
  destination_ranges      = []
  allows = []
  denies = []
}

module "service_account_1" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "test-vm-sa"
  display_name = "Test VM Service Account"
  description  = "Service account for test VMs"
}

module "service_account_2" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "test-app-sa"
  display_name = "Test App Service Account"
  description  = "Service account for test applications"
}

module "service_account_3" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "test-db-sa"
  display_name = "Test Database Service Account"
  description  = "Service account for test databases"
}

module "iam_binding_1" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:test-vm-sa@comprehensive-test-$(date +%s).iam.gserviceaccount.com"
  members = []
  condition = {"title": "Test condition", "expression": "request.time < timestamp('2025-12-31T23:59:59Z')", "description": "Time-based access control"}
}

module "iam_binding_2" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/compute.instanceAdmin"
  member  = "serviceAccount:test-app-sa@comprehensive-test-$(date +%s).iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_3" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:test-db-sa@comprehensive-test-$(date +%s).iam.gserviceaccount.com"
  members = []
  condition = null
}

module "pubsub_topic_1" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "test-events"
  labels  = {"purpose": "test", "type": "events"}
  subscriptions = [{"name": "test-events-subscription", "ack_deadline_seconds": 60, "retain_acked_messages": true, "message_retention_duration": "604800s"}]
}

module "pubsub_topic_2" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "test-notifications"
  labels  = {"purpose": "test", "type": "notifications"}
  subscriptions = [{"name": "test-notifications-push", "push_endpoint": "https://test-app.com/webhook", "oidc_service_account_email": "test-app-sa@comprehensive-test-$(date +%s).iam.gserviceaccount.com", "oidc_audience": "test-app-audience", "retry_min_backoff": "10s", "retry_max_backoff": "600s"}, {"name": "test-notifications-dlq", "dead_letter_topic": "test-failed-notifications", "max_delivery_attempts": 5, "filter": "attributes.status=\"failed\""}]
}

module "cloud_run_1" {
  source   = "../../modules/cloud_run"
  project_id = var.project_id
  name     = "test-cloud-run-1"
  location = "us-central1"
  image    = "nginxinc/nginx-unprivileged:stable-alpine"
  allow_unauthenticated = true
  vpc_connector = "test-vpc-connector"
  egress = "all-traffic"
  depends_on = [ module.serverless_vpc_connector_1 ]
}

module "cloud_run_2" {
  source   = "../../modules/cloud_run"
  project_id = var.project_id
  name     = "test-cloud-run-2"
  location = "us-west1"
  image    = "gcr.io/cloudrun/hello"
  allow_unauthenticated = false
}

module "cloud_sql_1" {
  source   = "../../modules/cloud_sql"
  project_id = var.project_id
  name             = "test-sql-postgres"
  database_version = "POSTGRES_14"
  region           = "us-central1"
  tier             = "db-f1-micro"
  deletion_protection = false
  availability_type = "ZONAL"
  disk_size = 20
  disk_type = "PD_SSD"
  ipv4_enabled = true
  private_network = null
  authorized_networks = [{"name": "test-network", "value": "0.0.0.0/0"}]
  backup_configuration = {"enabled": true, "start_time": "03:00", "location": "us", "point_in_time_recovery_enabled": true}
  maintenance_window = {"day": 7, "hour": 3}
  database_flags = [{"name": "log_statement", "value": "all"}]
  insights_config = null
  kms_key_name = null
}

module "cloud_sql_2" {
  source   = "../../modules/cloud_sql"
  project_id = var.project_id
  name             = "test-sql-mysql"
  database_version = "MYSQL_8_0"
  region           = "us-west1"
  tier             = "db-f1-micro"
  deletion_protection = false
  availability_type = null
  disk_size = null
  disk_type = null
  ipv4_enabled = false
  private_network = "test-vpc"
  authorized_networks = []
  backup_configuration = null
  maintenance_window = null
  database_flags = []
  insights_config = null
  kms_key_name = null
}

module "artifact_registry_1" {
  source   = "../../modules/artifact_registry"
  project_id = var.project_id
  name      = "test-docker-repo"
  location  = "us"
  format    = "DOCKER"
  description = "Docker repository for testing"
}

module "artifact_registry_2" {
  source   = "../../modules/artifact_registry"
  project_id = var.project_id
  name      = "test-maven-repo"
  location  = "us-central1"
  format    = "MAVEN"
  description = "Maven repository for testing"
}

module "secret_1" {
  source   = "../../modules/secret_manager"
  project_id = var.project_id
  name    = "test-api-key"
  value   = "test-secret-value-123"
  replication = "automatic"
  additional_versions = []
}

module "secret_2" {
  source   = "../../modules/secret_manager"
  project_id = var.project_id
  name    = "test-db-password"
  value   = "test-db-password-456"
  replication = "user_managed"
  additional_versions = []
}

module "secret_3" {
  source   = "../../modules/secret_manager"
  project_id = var.project_id
  name    = "test-jwt-secret"
  value   = "test-jwt-secret-789"
  replication = null
  additional_versions = [{"value": "old-jwt-secret-abc", "enabled": false}]
}

module "dns_zone_1" {
  source   = "../../modules/cloud_dns"
  project_id = var.project_id
  name     = "test-public-zone"
  dns_name = "test.example.com."
  description = "Public DNS zone for testing"
  record_sets = [{"name": "test.example.com.", "type": "A", "ttl": 300, "rrdatas": ["1.2.3.4"]}, {"name": "www.test.example.com.", "type": "CNAME", "ttl": 300, "rrdatas": ["test.example.com."]}, {"name": "api.test.example.com.", "type": "A", "ttl": 300, "rrdatas": ["5.6.7.8"]}]
}

module "dns_zone_2" {
  source   = "../../modules/cloud_dns"
  project_id = var.project_id
  name     = "test-private-zone"
  dns_name = "test.internal."
  description = "Private DNS zone for testing"
  record_sets = [{"name": "db.test.internal.", "type": "A", "ttl": 300, "rrdatas": ["10.10.0.100"]}, {"name": "cache.test.internal.", "type": "CNAME", "ttl": 300, "rrdatas": ["redis.test.internal."]}]
}

module "static_ip_1" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "test-external-ip"
  address_type = "EXTERNAL"
  region       = "us-central1"
  network_tier = "PREMIUM"
  subnetwork   = null
  purpose      = null
  address      = null
  description  = "External static IP for testing"
}

module "static_ip_2" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "test-internal-ip"
  address_type = "INTERNAL"
  region       = "us-central1"
  network_tier = null
  subnetwork   = "test-subnet-1"
  purpose      = "GCE_ENDPOINT"
  address      = "10.10.0.100"
  description  = "Internal static IP for testing"
}

module "static_ip_3" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "test-global-ip"
  address_type = "EXTERNAL"
  region       = null
  network_tier = "PREMIUM"
  subnetwork   = null
  purpose      = null
  address      = null
  description  = "Global static IP for testing"
}

module "compute_instance_1" {
  source   = "../../modules/compute_instance"
  project_id   = var.project_id
  name         = "test-vm-1"
  zone         = "us-central1-a"
  machine_type = "e2-micro"
  image        = "debian-cloud/debian-11"
  subnetwork   = "test-subnet-1"
  create_public_ip = false
  tags = ["ssh", "web"]
  depends_on = [ module.subnet_1 ]
}

module "compute_instance_2" {
  source   = "../../modules/compute_instance"
  project_id   = var.project_id
  name         = "test-vm-2"
  zone         = "us-west1-a"
  machine_type = "e2-small"
  image        = "ubuntu-os-cloud/ubuntu-2004-lts"
  subnetwork   = "test-subnet-2"
  create_public_ip = false
  tags = ["ssh"]
  depends_on = [ module.subnet_2 ]
}

module "disk_1" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "test-disk-standard"
  zone     = "us-central1-a"
  size_gb  = 100
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"purpose": "test", "type": "standard"}
  kms_key_self_link = null
}

module "disk_2" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "test-disk-ssd"
  zone     = "us-central1-a"
  size_gb  = 50
  type     = "pd-ssd"
  image    = null
  snapshot = null
  labels   = {"purpose": "test", "type": "ssd"}
  kms_key_self_link = null
}

module "disk_3" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "test-disk-balanced"
  zone     = "us-central1-a"
  size_gb  = 200
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"purpose": "test", "type": "balanced"}
  kms_key_self_link = null
}

module "bigquery_dataset_1" {
  source    = "../../modules/bigquery_dataset"
  project_id = var.project_id
  dataset_id = "test_analytics"
  location   = "US"
  labels     = {"purpose": "test", "type": "analytics"}
}

module "bigquery_dataset_2" {
  source    = "../../modules/bigquery_dataset"
  project_id = var.project_id
  dataset_id = "test_warehouse"
  location   = "us-central1"
  labels     = {"purpose": "test", "type": "warehouse"}
}

module "cloud_function_1" {
  source       = "../../modules/cloud_functions"
  project_id   = var.project_id
  name         = "test-function-http"
  location     = "us-central1"
  description  = null
  runtime      = "python311"
  entry_point  = "main"
  source_bucket = "test-functions-bucket"
  source_object = "functions/http-function.zip"
  memory       = "256M"
  timeout_seconds = 60
  ingress_settings = "ALLOW_ALL"
  max_instance_count = 1
}

module "cloud_function_2" {
  source       = "../../modules/cloud_functions"
  project_id   = var.project_id
  name         = "test-function-pubsub"
  location     = "us-central1"
  description  = null
  runtime      = "python311"
  entry_point  = "main"
  source_bucket = "test-functions-bucket"
  source_object = "functions/pubsub-function.zip"
  memory       = "256M"
  timeout_seconds = 60
  ingress_settings = "ALLOW_ALL"
  max_instance_count = 1
}

module "gke" {
  source        = "../../modules/gke"
  project_id    = var.project_id
  name          = "test-gke-cluster"
  location      = "us-central1"
  node_pool_name = "test-node-pool"
  node_count    = 1
  machine_type  = "e2-standard-2"
  labels        = {}
  tags          = []
  network       = "test-vpc"
  subnetwork    = "test-subnet-1"
  cluster_secondary_range_name  = "pods"
  services_secondary_range_name = "services"
  enable_private_nodes = true
  master_ipv4_cidr_block = "172.16.0.0/28"
  enable_network_policy = true
  node_auto_scaling = null
  node_labels = {}
  node_taints = []
}

module "cloud_router" {
  source    = "../../modules/cloud_router"
  project_id = var.project_id
  name      = "test-router"
  region    = "us-central1"
  network   = "test-vpc"
  asn       = 65001
  bgp_advertised_ip_ranges = [{"range": "10.10.0.0/24", "description": "Test subnet range"}]
  interfaces = []
  bgp_peers  = []
}

module "cloud_nat" {
  source    = "../../modules/cloud_nat"
  project_id = var.project_id
  name      = "test-nat"
  region    = "us-central1"
  router    = "test-router"
  nat_ip_allocation = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

module "serverless_vpc_connector_1" {
  source    = "../../modules/serverless_vpc_connector"
  project_id = var.project_id
  name       = "test-vpc-connector"
  region     = "us-central1"
  network    = "test-vpc"
  ip_cidr_range = "10.8.0.0/28"
}
