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
  name        = "dev-intern-proj-a-logs-h"
  location    = "US"
  uniform_bucket_level_access = true
  enable_versioning = true
  force_destroy = false
  storage_class = null
  public_access_prevention = null
  default_kms_key_name = null
  logging = null
  cors = []
  lifecycle_rules = []
  retention_policy = null
  labels = {"purpose": "logs"}
}
