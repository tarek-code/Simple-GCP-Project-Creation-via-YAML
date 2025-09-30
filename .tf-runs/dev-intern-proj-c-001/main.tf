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
}


# Additional resources from YAML
module "cloud_run_1" {
  source   = "../../modules/cloud_run"
  project_id = var.project_id
  name     = "hello-c"
  location = "us-central1"
  image    = "gcr.io/cloudrun/hello"
}

module "cloud_sql_1" {
  source   = "../../modules/cloud_sql"
  project_id = var.project_id
  name             = "sql-c"
  database_version = "POSTGRES_14"
  region           = "us-central1"
  tier             = "db-f1-micro"
}

module "secret_1" {
  source   = "../../modules/secret_manager"
  project_id = var.project_id
  name    = "api-token"
  value   = "dummy-value-change-me"
}

module "dns_zone_1" {
  source   = "../../modules/cloud_dns"
  project_id = var.project_id
  name     = "example-zone"
  dns_name = "example.internal."
  description = "Example internal zone"
}
