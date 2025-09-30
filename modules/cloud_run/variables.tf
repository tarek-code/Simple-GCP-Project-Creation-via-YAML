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
  default     = "gcr.io/cloudrun/hello"
}

variable "allow_unauthenticated" {
  description = "Grant public invoker to allUsers"
  type        = bool
  default     = false
}

variable "vpc_connector" {
  description = "Name of Serverless VPC connector to attach (optional)"
  type        = string
  default     = null
}

variable "egress" {
  description = "VPC egress setting: ALL_TRAFFIC or PRIVATE_RANGES_ONLY"
  type        = string
  default     = null
}


