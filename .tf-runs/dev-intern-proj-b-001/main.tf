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
module "pubsub_topic_1" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "events-b"
  labels  = {}
}

module "artifact_registry_1" {
  source   = "../../modules/artifact_registry"
  project_id = var.project_id
  name      = "docker-repo-b"
  location  = "us"
  format    = "DOCKER"
  description = null
}

module "compute_instance_1" {
  source   = "../../modules/compute_instance"
  project_id   = var.project_id
  name         = "vm-b1"
  zone         = "us-central1-a"
  machine_type = "e2-micro"
  image        = "debian-cloud/debian-11"
  subnetwork   = "default"
  create_public_ip = false
  tags = ["internal"]
}

module "compute_instance_2" {
  source   = "../../modules/compute_instance"
  project_id   = var.project_id
  name         = "vm-b2"
  zone         = "us-central1-b"
  machine_type = "e2-micro"
  image        = "debian-cloud/debian-11"
  subnetwork   = "default"
  create_public_ip = false
  tags = ["internal"]
}
