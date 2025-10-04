resource "google_compute_subnetwork" "subnet" {
  name                     = var.name
  project                  = var.project_id
  region                   = var.region
  ip_cidr_range            = var.ip_cidr_range
  network                  = var.network
  private_ip_google_access = var.private_ip_google_access
  purpose                  = var.purpose

  dynamic "secondary_ip_range" {
    for_each = var.secondary_ip_ranges
    content {
      range_name    = secondary_ip_range.value.range_name
      ip_cidr_range = secondary_ip_range.value.ip_cidr_range
    }
  }
}


