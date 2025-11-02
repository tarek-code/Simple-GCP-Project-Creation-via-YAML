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
variable "description" {
  description = "Instance description"
  type        = string
  default     = null
}

variable "metadata" {
  description = "Instance metadata (key -> value)"
  type        = map(string)
  default     = {}
}

variable "labels" {
  description = "Instance labels"
  type        = map(string)
  default     = {}
}

variable "metadata_startup_script" {
  description = "Startup script contents"
  type        = string
  default     = null
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

variable "allow_stopping_for_update" {
  description = "Allow stopping for update when changing fields like machine_type"
  type        = bool
  default     = true
}

variable "can_ip_forward" {
  description = "Allow sending/receiving packets with non-matching IPs"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "hostname" {
  description = "Custom hostname (FQDN)"
  type        = string
  default     = null
}

variable "min_cpu_platform" {
  description = "Minimum CPU platform"
  type        = string
  default     = null
}

variable "scheduling_preemptible" {
  description = "Preemptible/Spot VM"
  type        = bool
  default     = false
}

variable "scheduling_automatic_restart" {
  description = "Automatic restart"
  type        = bool
  default     = true
}

variable "scheduling_on_host_maintenance" {
  description = "On host maintenance action (MIGRATE or TERMINATE)"
  type        = string
  default     = null
}

variable "scheduling_provisioning_model" {
  description = "Provisioning model (STANDARD or SPOT)"
  type        = string
  default     = null
}

variable "enable_display" {
  description = "Enable virtual display device"
  type        = bool
  default     = false
}

variable "enable_confidential_compute" {
  description = "Enable confidential compute"
  type        = bool
  default     = false
}

variable "confidential_instance_type" {
  description = "Confidential instance type (SEV, SEV_SNP, TDX)"
  type        = string
  default     = null
}

variable "guest_accelerators" {
  description = "Guest accelerators (GPUs)"
  type = list(object({
    type  = string
    count = number
  }))
  default = []
}

# Boot disk advanced
variable "boot_disk_size_gb" {
  description = "Boot disk size (GB)"
  type        = number
  default     = null
}

variable "boot_disk_type" {
  description = "Boot disk type (pd-standard, pd-balanced, pd-ssd)"
  type        = string
  default     = null
}

variable "boot_disk_auto_delete" {
  description = "Auto-delete boot disk on instance deletion"
  type        = bool
  default     = true
}

variable "boot_disk_labels" {
  description = "Labels for boot disk"
  type        = map(string)
  default     = {}
}

# Network interface advanced
variable "network" {
  description = "Network name/self_link (optional if subnetwork given)"
  type        = string
  default     = null
}

variable "network_ip" {
  description = "Primary internal IP address"
  type        = string
  default     = null
}

variable "assign_external_ip" {
  description = "Assign ephemeral external IPv4"
  type        = bool
  default     = false
}

variable "external_network_tier" {
  description = "External IP network tier (PREMIUM, STANDARD)"
  type        = string
  default     = null
}

variable "advanced_machine_features" {
  description = "Advanced machine features: threads_per_core, visible_core_count, turbo_mode"
  type = object({
    threads_per_core   = optional(number)
    visible_core_count = optional(number)
    turbo_mode         = optional(string)
  })
  default = null
}


