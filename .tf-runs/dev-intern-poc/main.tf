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
module "subnet_1" {
  source  = "../../modules/subnet"
  project_id     = var.project_id
  name           = "demo-subnet"
  region         = "us-central1"
  ip_cidr_range  = "10.0.0.0/24"
  network        = "demo-vpc"
  private_ip_google_access = true
  purpose        = null
  secondary_ip_ranges = []
}

module "static_ip_1" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "web-server-external-ip"
  address_type = "EXTERNAL"
  region       = "us-central1"
  network_tier = "PREMIUM"
  subnetwork   = null
  purpose      = null
  address      = null
  description  = "External static IP for web server"
}

module "static_ip_2" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "global-lb-ip"
  address_type = "EXTERNAL"
  region       = null
  network_tier = "PREMIUM"
  subnetwork   = null
  purpose      = null
  address      = null
  description  = "Global static IP for load balancer"
}

module "static_ip_3" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "internal-api-ip"
  address_type = "INTERNAL"
  region       = "us-central1"
  network_tier = null
  subnetwork   = "demo-subnet"
  purpose      = "GCE_ENDPOINT"
  address      = null
  description  = "Internal static IP for API server"
}

module "static_ip_4" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "database-internal-ip"
  address_type = "INTERNAL"
  region       = "us-central1"
  network_tier = null
  subnetwork   = "demo-subnet"
  purpose      = "GCE_ENDPOINT"
  address      = "10.0.0.100"
  description  = "Internal static IP for database (fixed address)"
}

module "static_ip_5" {
  source   = "../../modules/static_ip"
  project_id  = var.project_id
  name        = "peering-internal-ip"
  address_type = "INTERNAL"
  region       = "us-central1"
  network_tier = null
  subnetwork   = "demo-subnet"
  purpose      = "VPC_PEERING"
  address      = null
  description  = "Internal IP for VPC peering"
}

module "compute_instance_1" {
  source   = "../../modules/compute_instance"
  project_id   = var.project_id
  name         = "web-server"
  zone         = "us-central1-a"
  machine_type = "e2-micro"
  image        = "debian-cloud/debian-11"
  subnetwork   = "demo-subnet"
  create_public_ip = false
  tags = ["web", "http-server"]
  depends_on = [ module.subnet_1 ]
}
