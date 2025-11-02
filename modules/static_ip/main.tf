locals {
  is_regional = var.region != null && var.region != ""
}

resource "google_compute_address" "ip_regional" {
  count        = local.is_regional ? 1 : 0
  project      = var.project_id
  name         = var.name
  address_type = var.address_type
  region       = var.region
  description  = var.description
  address      = var.address

  # INTERNAL specifics
  purpose      = var.purpose
  subnetwork   = var.subnetwork
  network_tier = var.network_tier
}

resource "google_compute_global_address" "ip_global" {
  count       = local.is_regional ? 0 : 1
  project     = var.project_id
  name        = var.name
  description = var.description
  address     = var.address
}

output "self_link" {
  value = local.is_regional ? google_compute_address.ip_regional[0].self_link : google_compute_global_address.ip_global[0].self_link
}

