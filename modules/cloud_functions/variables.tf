variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Function name"
  type        = string
}

variable "location" {
  description = "Region"
  type        = string
  default     = "us-central1"
}

variable "description" {
  description = "Function description"
  type        = string
  default     = null
}

variable "runtime" {
  description = "Runtime (e.g., nodejs20, python311)"
  type        = string
}

variable "entry_point" {
  description = "Entrypoint function"
  type        = string
}

variable "source_bucket" {
  description = "Source bucket"
  type        = string
}

variable "source_object" {
  description = "Source object path"
  type        = string
}

variable "memory" {
  description = "Available memory (e.g., 256M)"
  type        = string
  default     = "256M"
}

variable "timeout_seconds" {
  description = "Timeout seconds"
  type        = number
  default     = 60
}

variable "ingress_settings" {
  description = "Ingress settings"
  type        = string
  default     = "ALLOW_ALL"
}

variable "max_instance_count" {
  description = "Max instances"
  type        = number
  default     = 1
}


