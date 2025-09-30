variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Managed zone name"
  type        = string
}

variable "dns_name" {
  description = "DNS name (must end with a dot)"
  type        = string
}

variable "description" {
  description = "Zone description"
  type        = string
  default     = null
}


