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
module "storage_bucket_1" {
  source  = "../../modules/storage_bucket"
  project_id = var.project_id
  name        = "dev-intern-proj-a-logs"
  location    = "US"
  uniform_bucket_level_access = true
  enable_versioning = true
  labels = {"purpose": "logs"}
}

module "vpc" {
  source  = "../../modules/vpc"
  project_id   = var.project_id
  name         = "vpc-a"
  routing_mode = "GLOBAL"
  description  = null
}

module "subnet_1" {
  source  = "../../modules/subnet"
  project_id     = var.project_id
  name           = "subnet-a1"
  region         = "us-central1"
  ip_cidr_range  = "10.10.0.0/24"
  network        = "vpc-a"
  private_ip_google_access = true
  purpose        = null
}

module "compute_instance_1" {
  source   = "../../modules/compute_instance"
  project_id   = var.project_id
  name         = "vm-a1"
  zone         = "us-central1-a"
  machine_type = "e2-micro"
  image        = "debian-cloud/debian-11"
  subnetwork   = "subnet-a1"
  create_public_ip = true
  tags = ["ssh"]
}
