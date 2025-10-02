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
  create_project  = false
}


# Additional resources from YAML
module "vpc" {
  source  = "../../modules/vpc"
  project_id   = var.project_id
  name         = "vpc-run"
  routing_mode = "GLOBAL"
  description  = null
}

module "subnet_1" {
  source  = "../../modules/subnet"
  project_id     = var.project_id
  name           = "subnet-run"
  region         = "us-central1"
  ip_cidr_range  = "10.20.0.0/24"
  network        = "vpc-run"
  private_ip_google_access = true
  purpose        = null
  secondary_ip_ranges = []
}

module "cloud_run_1" {
  source   = "../../modules/cloud_run"
  project_id = var.project_id
  name     = "hello-run"
  location = "us-central1"
  image    = "nginxinc/nginx-unprivileged:stable-alpine"
  allow_unauthenticated = true
  vpc_connector = "run-connector"
  egress = "all-traffic"
  depends_on = [ module.serverless_vpc_connector_1 ]
}

module "serverless_vpc_connector_1" {
  source    = "../../modules/serverless_vpc_connector"
  project_id = var.project_id
  name       = "run-connector"
  region     = "us-central1"
  network    = "vpc-run"
  ip_cidr_range = "10.8.0.0/28"
}
