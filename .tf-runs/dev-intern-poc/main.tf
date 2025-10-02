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
module "disk_1" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "data-storage-disk"
  zone     = "us-central1-a"
  size_gb  = 100
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"role": "data-storage", "env": "dev", "purpose": "general-data"}
  kms_key_self_link = null
}

module "disk_2" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "cache-disk"
  zone     = "us-central1-a"
  size_gb  = 50
  type     = "pd-ssd"
  image    = null
  snapshot = null
  labels   = {"role": "cache", "env": "dev", "purpose": "high-performance-cache"}
  kms_key_self_link = null
}

module "disk_3" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "app-data-disk"
  zone     = "us-central1-a"
  size_gb  = 200
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "application", "env": "dev", "purpose": "app-storage"}
  kms_key_self_link = null
}

module "disk_4" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "boot-disk-debian"
  zone     = "us-central1-a"
  size_gb  = 20
  type     = "pd-ssd"
  image    = "projects/debian-cloud/global/images/family/debian-11"
  snapshot = null
  labels   = {"role": "boot", "env": "dev", "os": "debian-11"}
  kms_key_self_link = null
}

module "disk_5" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "boot-disk-ubuntu"
  zone     = "us-central1-a"
  size_gb  = 25
  type     = "pd-balanced"
  image    = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2004-lts"
  snapshot = null
  labels   = {"role": "boot", "env": "dev", "os": "ubuntu-20.04"}
  kms_key_self_link = null
}

module "disk_6" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "database-disk"
  zone     = "us-central1-a"
  size_gb  = 500
  type     = "pd-ssd"
  image    = null
  snapshot = null
  labels   = {"role": "database", "env": "dev", "purpose": "postgresql-data"}
  kms_key_self_link = null
}

module "disk_7" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "backup-disk"
  zone     = "us-central1-a"
  size_gb  = 1000
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"role": "backup", "env": "dev", "purpose": "daily-backups"}
  kms_key_self_link = null
}

module "disk_8" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "log-disk"
  zone     = "us-central1-a"
  size_gb  = 100
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"role": "logging", "env": "dev", "purpose": "application-logs"}
  kms_key_self_link = null
}

module "disk_9" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "temp-processing-disk"
  zone     = "us-central1-a"
  size_gb  = 200
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "temporary", "env": "dev", "purpose": "data-processing"}
  kms_key_self_link = null
}

module "disk_10" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "dev-test-disk"
  zone     = "us-central1-a"
  size_gb  = 50
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"role": "development", "env": "dev", "purpose": "testing"}
  kms_key_self_link = null
}

module "disk_11" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "data-disk-central-b"
  zone     = "us-central1-b"
  size_gb  = 150
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "data-storage", "env": "dev", "zone": "central-b"}
  kms_key_self_link = null
}

module "disk_12" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "data-disk-central-c"
  zone     = "us-central1-c"
  size_gb  = 150
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "data-storage", "env": "dev", "zone": "central-c"}
  kms_key_self_link = null
}

module "disk_13" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "analytics-disk"
  zone     = "us-central1-a"
  size_gb  = 1000
  type     = "pd-ssd"
  image    = null
  snapshot = null
  labels   = {"role": "analytics", "env": "dev", "purpose": "big-data-processing"}
  kms_key_self_link = null
}

module "disk_14" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "archive-disk"
  zone     = "us-central1-a"
  size_gb  = 2000
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"role": "archive", "env": "dev", "purpose": "long-term-storage"}
  kms_key_self_link = null
}

module "disk_15" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "monitoring-disk"
  zone     = "us-central1-a"
  size_gb  = 100
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "monitoring", "env": "dev", "purpose": "metrics-storage"}
  kms_key_self_link = null
}

module "disk_16" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "security-audit-disk"
  zone     = "us-central1-a"
  size_gb  = 200
  type     = "pd-ssd"
  image    = null
  snapshot = null
  labels   = {"role": "security", "env": "dev", "purpose": "audit-logs"}
  kms_key_self_link = null
}

module "disk_17" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "container-volume-disk"
  zone     = "us-central1-a"
  size_gb  = 300
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "container", "env": "dev", "purpose": "docker-volumes"}
  kms_key_self_link = null
}

module "disk_18" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "cicd-artifacts-disk"
  zone     = "us-central1-a"
  size_gb  = 500
  type     = "pd-standard"
  image    = null
  snapshot = null
  labels   = {"role": "cicd", "env": "dev", "purpose": "build-artifacts"}
  kms_key_self_link = null
}

module "disk_19" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "ml-datasets-disk"
  zone     = "us-central1-a"
  size_gb  = 2000
  type     = "pd-ssd"
  image    = null
  snapshot = null
  labels   = {"role": "machine-learning", "env": "dev", "purpose": "training-datasets"}
  kms_key_self_link = null
}

module "disk_20" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "web-content-disk"
  zone     = "us-central1-a"
  size_gb  = 100
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "web-server", "env": "dev", "purpose": "static-content"}
  kms_key_self_link = null
}

module "disk_21" {
  source   = "../../modules/compute_disk"
  project_id = var.project_id
  name     = "api-data-disk"
  zone     = "us-central1-a"
  size_gb  = 250
  type     = "pd-balanced"
  image    = null
  snapshot = null
  labels   = {"role": "api-server", "env": "dev", "purpose": "application-data"}
  kms_key_self_link = null
}
