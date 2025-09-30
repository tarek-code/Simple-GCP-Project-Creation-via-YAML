resource "google_compute_router_nat" "nat" {
  name                               = var.name
  project                            = var.project_id
  region                             = var.region
  router                             = var.router
  nat_ip_allocate_option             = var.nat_ip_allocation
  source_subnetwork_ip_ranges_to_nat = var.source_subnetwork_ip_ranges_to_nat
}


