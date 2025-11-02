variable "project_id" {
  description = "Project ID"
  type        = string
}

variable "name" {
  description = "Disk name"
  type        = string
}

variable "zone" {
  description = "Zone for the disk"
  type        = string
}

variable "size_gb" {
  description = "Disk size in GB"
  type        = number
  default     = 10
}

variable "type" {
  description = "Disk type, e.g., pd-standard, pd-ssd, pd-balanced"
  type        = string
  default     = "pd-standard"
}

variable "image" {
  description = "Source image (optional)"
  type        = string
  default     = null
}

variable "snapshot" {
  description = "Source snapshot (optional)"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels for the disk"
  type        = map(string)
  default     = {}
}

variable "kms_key_self_link" {
  description = "CMEK key for encryption (optional)"
  type        = string
  default     = null
}

