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


