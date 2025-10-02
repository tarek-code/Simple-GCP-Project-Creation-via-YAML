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
  name        = "web-app-assets-bucket"
  location    = "US"
  uniform_bucket_level_access = true
  enable_versioning = false
  force_destroy = false
  storage_class = null
  public_access_prevention = null
  default_kms_key_name = null
  logging = null
  cors = []
  lifecycle_rules = []
  retention_policy = null
  labels = {"purpose": "web-assets", "service": "web-app"}
}

module "storage_bucket_2" {
  source  = "../../modules/storage_bucket"
  project_id = var.project_id
  name        = "backup-storage-bucket"
  location    = "US"
  uniform_bucket_level_access = true
  enable_versioning = false
  force_destroy = false
  storage_class = null
  public_access_prevention = null
  default_kms_key_name = null
  logging = null
  cors = []
  lifecycle_rules = []
  retention_policy = null
  labels = {"purpose": "backups", "service": "backup-service"}
}

module "service_account_1" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "web-app-service"
  display_name = "Web Application Service Account"
  description  = "Service account for web application operations and API access"
}

module "service_account_2" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "database-service"
  display_name = "Database Service Account"
  description  = "Service account for database connections and operations"
}

module "service_account_3" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "cicd-pipeline"
  display_name = "CI/CD Pipeline Service Account"
  description  = "Service account for continuous integration and deployment"
}

module "service_account_4" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "monitoring-agent"
  display_name = "Monitoring Agent Service Account"
  description  = "Service account for monitoring, logging, and metrics collection"
}

module "service_account_5" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "storage-service"
  display_name = "Storage Service Account"
  description  = "Service account for file storage operations and backups"
}

module "service_account_6" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "pubsub-service"
  display_name = "Pub/Sub Service Account"
  description  = "Service account for message publishing and subscription"
}

module "service_account_7" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "compute-service"
  display_name = "Compute Service Account"
  description  = "Service account for VM and container operations"
}

module "service_account_8" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "security-service"
  display_name = "Security Service Account"
  description  = "Service account for security scanning and compliance checks"
}

module "service_account_9" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "analytics-service"
  display_name = "Analytics Service Account"
  description  = "Service account for data analytics and reporting"
}

module "service_account_10" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "backup-service"
  display_name = "Backup Service Account"
  description  = "Service account for automated backup operations"
}

module "iam_binding_1" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:web-app-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_2" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:web-app-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_3" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:database-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_4" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:database-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_5" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:cicd-pipeline@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_6" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:cicd-pipeline@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_7" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:cicd-pipeline@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_8" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:monitoring-agent@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_9" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:monitoring-agent@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_10" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:monitoring-agent@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_11" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:storage-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_12" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/storage.legacyBucketReader"
  member  = "serviceAccount:storage-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_13" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:pubsub-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_14" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:pubsub-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_15" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/pubsub.admin"
  member  = "serviceAccount:pubsub-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_16" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/compute.instanceAdmin"
  member  = "serviceAccount:compute-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_17" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/compute.networkAdmin"
  member  = "serviceAccount:compute-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_18" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/securitycenter.findingsEditor"
  member  = "serviceAccount:security-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_19" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/cloudasset.viewer"
  member  = "serviceAccount:security-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_20" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:analytics-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_21" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:analytics-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_22" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:backup-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "iam_binding_23" {
  source  = "../../modules/iam_binding"
  project_id = var.project_id
  role    = "roles/compute.storageAdmin"
  member  = "serviceAccount:backup-service@dev-intern-poc.iam.gserviceaccount.com"
  members = []
  condition = null
}

module "pubsub_topic_1" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "web-app-events"
  labels  = {"service": "web-app", "purpose": "events"}
  subscriptions = []
}

module "pubsub_topic_2" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "monitoring-alerts"
  labels  = {"service": "monitoring", "purpose": "alerts"}
  subscriptions = []
}
