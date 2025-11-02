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
  source_tags             = length(var.source_tags) > 0 ? var.source_tags : null
  source_service_accounts = length(var.source_service_accounts) > 0 ? var.source_service_accounts : null
  target_tags             = length(var.target_tags) > 0 ? var.target_tags : null
  target_service_accounts = length(var.target_service_accounts) > 0 ? var.target_service_accounts : null
  destination_ranges      = var.destination_ranges
  disabled                = var.disabled
  description             = var.description

  dynamic "log_config" {
    for_each = var.enable_logging && var.log_config != null ? [var.log_config] : []
    content {
      metadata = log_config.value.metadata
    }
  }
}


