resource "google_compute_firewall" "rules" {
  name    = var.name
  project = var.project_id
  network = var.network

  direction = var.direction
  priority  = var.priority

  dynamic "allow" {
    for_each = length(var.allows) > 0 ? var.allows : (var.protocol == null ? [] : [
      {
        protocol = var.protocol
        ports    = var.ports
      }
    ])
    content {
      protocol = allow.value.protocol
      ports    = try(allow.value.ports, null)
    }
  }

  dynamic "deny" {
    for_each = var.denies
    content {
      protocol = deny.value.protocol
      ports    = try(deny.value.ports, null)
    }
  }

  source_ranges           = var.source_ranges
  target_tags             = var.target_tags
  target_service_accounts = var.target_service_accounts
  destination_ranges      = var.destination_ranges
}


