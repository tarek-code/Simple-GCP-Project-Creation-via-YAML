variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Instance name"
  type        = string
}

variable "zone" {
  description = "Zone (e.g., us-central1-a)"
  type        = string
}

variable "machine_type" {
  description = "Machine type (e.g., e2-micro)"
  type        = string
}

variable "image" {
  description = "Boot image (e.g., debian-cloud/debian-11)"
  type        = string
}

variable "subnetwork" {
  description = "Subnetwork self link or name"
  type        = string
  default     = null
}

variable "create_public_ip" {
  description = "Create ephemeral public IP"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Network tags"
  type        = list(string)
  default     = []
}


# Advanced optional inputs
variable "metadata" {
  description = "Instance metadata (key -> value)"
  type        = map(string)
  default     = {}
}

variable "service_account_email" {
  description = "Service account email to attach (optional)"
  type        = string
  default     = null
}

variable "service_account_scopes" {
  description = "OAuth scopes for service account (optional)"
  type        = list(string)
  default     = ["https://www.googleapis.com/auth/cloud-platform"]
}

variable "additional_disks" {
  description = "Additional persistent disks to create and attach"
  type = list(object({
    name        = string
    size_gb     = number
    type        = string
    auto_delete = optional(bool, true)
  }))
  default = []
}

variable "enable_shielded_vm" {
  description = "Enable Shielded VM options"
  type        = bool
  default     = false
}

variable "shielded_secure_boot" {
  description = "Shielded VM secure boot"
  type        = bool
  default     = false
}

variable "shielded_vtpm" {
  description = "Shielded VM vTPM"
  type        = bool
  default     = true
}

variable "shielded_integrity_monitoring" {
  description = "Shielded VM integrity monitoring"
  type        = bool
  default     = true
}


