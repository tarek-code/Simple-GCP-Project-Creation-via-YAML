resource "google_compute_subnetwork" "subnet" {
  name                     = var.name
  project                  = var.project_id
  region                   = var.region
  ip_cidr_range            = var.ip_cidr_range
  network                  = var.network
  private_ip_google_access = var.private_ip_google_access
  purpose                  = var.purpose

  description             = var.description
  reserved_internal_range = var.reserved_internal_range
  role                    = var.role

  private_ipv6_google_access = var.private_ipv6_google_access

  # IPv6 Configuration
  stack_type           = var.stack_type
  ipv6_access_type     = var.ipv6_access_type
  external_ipv6_prefix = var.external_ipv6_prefix
  ip_collection        = var.ip_collection

  # Advanced Configuration
  # allow_subnet_cidr_routes_overlap = var.allow_subnet_cidr_routes_overlap  # Not supported in current Terraform version

  # Secondary IP Ranges (legacy)
  dynamic "secondary_ip_range" {
    for_each = var.secondary_ip_ranges
    content {
      range_name    = secondary_ip_range.value.range_name
      ip_cidr_range = secondary_ip_range.value.ip_cidr_range
    }
  }

  # Secondary IP Ranges (new format)
  dynamic "secondary_ip_range" {
    for_each = var.secondary_ip_range
    content {
      range_name              = secondary_ip_range.value.range_name
      ip_cidr_range           = secondary_ip_range.value.ip_cidr_range
      reserved_internal_range = secondary_ip_range.value.reserved_internal_range
    }
  }

  # Logging Configuration
  dynamic "log_config" {
    for_each = var.log_config != null ? [var.log_config] : []
    content {
      aggregation_interval = log_config.value.aggregation_interval
      flow_sampling        = log_config.value.flow_sampling
      metadata             = log_config.value.metadata
      metadata_fields      = log_config.value.metadata_fields
      filter_expr          = log_config.value.filter_expr
    }
  }

  # Resource Manager Tags
  dynamic "params" {
    for_each = length(var.resource_manager_tags) > 0 ? [var.resource_manager_tags] : []
    content {
      resource_manager_tags = params.value
    }
  }
}


