variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Subnetwork name"
  type        = string
}

variable "region" {
  description = "Subnetwork region"
  type        = string
}

variable "ip_cidr_range" {
  description = "CIDR range for the subnet"
  type        = string
}

variable "network" {
  description = "Self link or name of the VPC network"
  type        = string
}

variable "private_ip_google_access" {
  description = "Enable Private Google Access"
  type        = bool
  default     = true
}

variable "purpose" {
  description = "SUBNETWORK purpose"
  type        = string
  default     = null
}

variable "secondary_ip_ranges" {
  description = "Secondary IP ranges (list of { range_name, ip_cidr_range })"
  type = list(object({
    range_name    = string
    ip_cidr_range = string
  }))
  default = []
}

variable "description" {
  description = "An optional description of this resource"
  type        = string
  default     = null
}

variable "reserved_internal_range" {
  description = "The ID of the reserved internal range"
  type        = string
  default     = null
}

variable "role" {
  description = "The role of subnetwork"
  type        = string
  default     = null
  validation {
    condition     = var.role == null || contains(["ACTIVE", "BACKUP"], var.role)
    error_message = "role must be ACTIVE or BACKUP."
  }
}

variable "secondary_ip_range" {
  description = "An array of configurations for secondary IP ranges"
  type = list(object({
    range_name              = string
    ip_cidr_range           = optional(string)
    reserved_internal_range = optional(string)
  }))
  default = []
}

variable "private_ipv6_google_access" {
  description = "The private IPv6 google access type for the VMs in this subnet"
  type        = string
  default     = null
}

variable "log_config" {
  description = "VPC flow logging options for this subnetwork"
  type = object({
    aggregation_interval = optional(string)
    flow_sampling        = optional(number)
    metadata             = optional(string)
    metadata_fields      = optional(list(string))
    filter_expr          = optional(string)
  })
  default = null
}

variable "stack_type" {
  description = "The stack type for this subnet to identify whether the IPv6 feature is enabled"
  type        = string
  default     = "IPV4_ONLY"
  validation {
    condition     = contains(["IPV4_ONLY", "IPV4_IPV6", "IPV6_ONLY"], var.stack_type)
    error_message = "stack_type must be IPV4_ONLY, IPV4_IPV6, or IPV6_ONLY."
  }
}

variable "ipv6_access_type" {
  description = "The access type of IPv6 address this subnet holds"
  type        = string
  default     = null
  validation {
    condition     = var.ipv6_access_type == null || contains(["EXTERNAL", "INTERNAL"], var.ipv6_access_type)
    error_message = "ipv6_access_type must be EXTERNAL or INTERNAL."
  }
}

variable "external_ipv6_prefix" {
  description = "The range of external IPv6 addresses that are owned by this subnetwork"
  type        = string
  default     = null
}

variable "ip_collection" {
  description = "Resource reference of a PublicDelegatedPrefix"
  type        = string
  default     = null
}

variable "allow_subnet_cidr_routes_overlap" {
  description = "Allow subnet CIDR routes overlap"
  type        = bool
  default     = false
}

variable "send_secondary_ip_range_if_empty" {
  description = "Controls the removal behavior of secondary_ip_range"
  type        = bool
  default     = false
}

variable "resource_manager_tags" {
  description = "Resource manager tags to be bound to the subnetwork"
  type        = map(string)
  default     = {}
}


