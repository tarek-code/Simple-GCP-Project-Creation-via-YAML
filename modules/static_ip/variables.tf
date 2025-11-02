variable "project_id" {
  description = "Project ID where the address is created"
  type        = string
}

variable "name" {
  description = "Name of the static IP address"
  type        = string
}

variable "address_type" {
  description = "Type of address: EXTERNAL or INTERNAL"
  type        = string
  default     = "EXTERNAL"
}

variable "region" {
  description = "Region for regional address. Omit for global address."
  type        = string
  default     = null
}

variable "network_tier" {
  description = "Network tier: PREMIUM or STANDARD (for external)"
  type        = string
  default     = null
}

variable "subnetwork" {
  description = "Subnetwork self link or name for INTERNAL addresses"
  type        = string
  default     = null
}

variable "purpose" {
  description = "Purpose for INTERNAL addresses (e.g., GCE_ENDPOINT, VPC_PEERING)"
  type        = string
  default     = null
}

variable "address" {
  description = "Optional static IP to assign; if null, Google allocates"
  type        = string
  default     = null
}

variable "description" {
  description = "Description for the address"
  type        = string
  default     = null
}

