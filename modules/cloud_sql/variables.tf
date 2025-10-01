variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Instance name"
  type        = string
}

variable "database_version" {
  description = "Database version (e.g., POSTGRES_14)"
  type        = string
  default     = "POSTGRES_14"
}

variable "region" {
  description = "Region for the instance"
  type        = string
  default     = "us-central1"
}

variable "tier" {
  description = "Machine type tier (e.g., db-f1-micro)"
  type        = string
  default     = "db-f1-micro"
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "availability_type" {
  description = "ZONAL or REGIONAL (for HA)"
  type        = string
  default     = null
}

variable "disk_size" {
  description = "Disk size (GB)"
  type        = number
  default     = null
}

variable "disk_type" {
  description = "PD_SSD or PD_HDD"
  type        = string
  default     = null
}

variable "authorized_networks" {
  description = "Authorized networks for IPv4 (list of { name, value })"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "ipv4_enabled" {
  description = "Enable public IPv4"
  type        = bool
  default     = false
}

variable "private_network" {
  description = "VPC network self link for private IP"
  type        = string
  default     = null
}

variable "backup_configuration" {
  description = "Backup config: { enabled, start_time, binary_log_enabled }"
  type = object({
    enabled            = bool
    start_time         = optional(string)
    binary_log_enabled = optional(bool)
  })
  default = null
}

variable "maintenance_window" {
  description = "Maintenance window: { day, hour, update_track }"
  type = object({
    day          = number
    hour         = number
    update_track = optional(string)
  })
  default = null
}

variable "database_flags" {
  description = "List of database flags: [{ name, value }]"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "insights_config" {
  description = "Insights config: { query_string_length, record_application_tags, record_client_address }"
  type = object({
    query_string_length     = optional(number)
    record_application_tags = optional(bool)
    record_client_address   = optional(bool)
  })
  default = null
}

variable "kms_key_name" {
  description = "CMEK key name"
  type        = string
  default     = null
}


