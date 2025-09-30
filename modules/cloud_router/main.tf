resource "google_compute_router" "router" {
  name    = var.name
  project = var.project_id
  region  = var.region
  network = var.network
}


