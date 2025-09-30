resource "google_compute_subnetwork" "subnet" {
  name                     = var.name
  project                  = var.project_id
  region                   = var.region
  ip_cidr_range            = var.ip_cidr_range
  network                  = var.network
  private_ip_google_access = var.private_ip_google_access
  purpose                  = var.purpose
}


