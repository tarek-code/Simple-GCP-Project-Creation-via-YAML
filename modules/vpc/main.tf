resource "google_compute_network" "vpc" {
  name                    = var.name
  project                 = var.project_id
  auto_create_subnetworks = var.auto_create_subnetworks
  routing_mode            = var.routing_mode
  description             = var.description
  mtu                     = var.mtu

  # BGP Configuration
  bgp_best_path_selection_mode = var.bgp_best_path_selection_mode
  bgp_always_compare_med       = var.bgp_always_compare_med
  bgp_inter_region_cost        = var.bgp_inter_region_cost

  # IPv6 Configuration
  enable_ula_internal_ipv6 = var.enable_ula_internal_ipv6
  internal_ipv6_range      = var.internal_ipv6_range

  # Firewall Policy Configuration
  network_firewall_policy_enforcement_order = var.network_firewall_policy_enforcement_order

  # Network Profile
  network_profile = var.network_profile

  # Route Configuration
  delete_default_routes_on_create = var.delete_default_routes_on_create

  # Resource Manager Tags
  dynamic "params" {
    for_each = length(var.resource_manager_tags) > 0 ? [var.resource_manager_tags] : []
    content {
      resource_manager_tags = params.value
    }
  }
}


