variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "VPC network name"
  type        = string
}

variable "routing_mode" {
  description = "Global or REGIONAL routing"
  type        = string
  default     = "GLOBAL"
}

variable "description" {
  description = "Network description"
  type        = string
  default     = null
}

variable "mtu" {
  description = "MTU for the VPC (1460-1500), optional"
  type        = number
  default     = null
}

variable "auto_create_subnetworks" {
  description = "When set to true, the network is created in auto subnet mode"
  type        = bool
  default     = false
}

variable "description" {
  description = "An optional description of this resource"
  type        = string
  default     = null
}

variable "bgp_best_path_selection_mode" {
  description = "The BGP best selection algorithm to be employed"
  type        = string
  default     = null
  validation {
    condition     = var.bgp_best_path_selection_mode == null || contains(["LEGACY", "STANDARD"], var.bgp_best_path_selection_mode)
    error_message = "bgp_best_path_selection_mode must be LEGACY or STANDARD."
  }
}

variable "bgp_always_compare_med" {
  description = "Enables/disables the comparison of MED across routes with different Neighbor ASNs"
  type        = bool
  default     = null
}

variable "bgp_inter_region_cost" {
  description = "Choice of the behavior of inter-regional cost and MED in the BPS algorithm"
  type        = string
  default     = null
  validation {
    condition     = var.bgp_inter_region_cost == null || contains(["DEFAULT", "ADD_COST_TO_MED"], var.bgp_inter_region_cost)
    error_message = "bgp_inter_region_cost must be DEFAULT or ADD_COST_TO_MED."
  }
}

variable "enable_ula_internal_ipv6" {
  description = "Enable ULA internal ipv6 on this network"
  type        = bool
  default     = false
}

variable "internal_ipv6_range" {
  description = "When enabling ula internal ipv6, caller optionally can specify the /48 range they want"
  type        = string
  default     = null
}

variable "network_firewall_policy_enforcement_order" {
  description = "Set the order that Firewall Rules and Firewall Policies are evaluated"
  type        = string
  default     = null
  validation {
    condition     = var.network_firewall_policy_enforcement_order == null || contains(["BEFORE_CLASSIC_FIREWALL", "AFTER_CLASSIC_FIREWALL"], var.network_firewall_policy_enforcement_order)
    error_message = "network_firewall_policy_enforcement_order must be BEFORE_CLASSIC_FIREWALL or AFTER_CLASSIC_FIREWALL."
  }
}

variable "network_profile" {
  description = "A full or partial URL of the network profile to apply to this network"
  type        = string
  default     = null
}

variable "delete_default_routes_on_create" {
  description = "If set to true, default routes (0.0.0.0/0) will be deleted immediately after network creation"
  type        = bool
  default     = false
}

variable "resource_manager_tags" {
  description = "Resource manager tags to be bound to the network"
  type        = map(string)
  default     = {}
}


