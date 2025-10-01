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

variable "maintenance_policy" {
  description = "Maintenance window: { day, start_time: { hours, minutes, seconds, nanos } }"
  type = object({
    day = number
    start_time = object({
      hours   = number
      minutes = optional(number)
      seconds = optional(number)
      nanos   = optional(number)
    })
  })
  default = null
}

variable "persistence_config" {
  description = "Persistence config: { persistence_mode, rdb_snapshot_period, rdb_snapshot_start_time }"
  type = object({
    persistence_mode        = string
    rdb_snapshot_period     = optional(string)
    rdb_snapshot_start_time = optional(string)
  })
  default = null
}


