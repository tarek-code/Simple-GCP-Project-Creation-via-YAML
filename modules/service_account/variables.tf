variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "account_id" {
  description = "Service account ID (no domain)"
  type        = string
}

variable "display_name" {
  description = "Service account display name"
  type        = string
  default     = null
}

variable "description" {
  description = "Service account description"
  type        = string
  default     = null
}


