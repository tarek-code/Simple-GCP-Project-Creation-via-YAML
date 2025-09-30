variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Cloud Run service name"
  type        = string
}

variable "location" {
  description = "Region for Cloud Run"
  type        = string
  default     = "us-central1"
}

variable "image" {
  description = "Container image"
  type        = string
}


