resource "google_compute_firewall" "rules" {
  name    = var.name
  project = var.project_id
  network = var.network

  direction = var.direction
  priority  = var.priority

  allow {
    protocol = var.protocol
    ports    = var.ports
  }

  source_ranges = var.source_ranges
  target_tags   = var.target_tags
}


