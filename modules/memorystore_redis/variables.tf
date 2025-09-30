variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Redis instance name"
  type        = string
}

variable "region" {
  description = "Region"
  type        = string
  default     = "us-central1"
}

variable "tier" {
  description = "Tier: BASIC or STANDARD_HA"
  type        = string
  default     = "BASIC"
}

variable "memory_size_gb" {
  description = "Memory size in GB"
  type        = number
  default     = 1
}

variable "redis_version" {
  description = "Redis version (e.g., REDIS_6_X)"
  type        = string
  default     = "REDIS_6_X"
}

variable "display_name" {
  description = "Display name"
  type        = string
  default     = null
}

variable "connect_mode" {
  description = "Connect mode (DIRECT_PEERING or PRIVATE_SERVICE_ACCESS)"
  type        = string
  default     = "DIRECT_PEERING"
}

variable "authorized_network" {
  description = "VPC network self link or name"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels"
  type        = map(string)
  default     = {}
}


