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


# Optional advanced settings
variable "env" {
  description = "Environment variables for the container (key -> value)"
  type        = map(string)
  default     = {}
}

variable "annotations" {
  description = "Additional annotations to merge into template metadata"
  type        = map(string)
  default     = {}
}

variable "container_port" {
  description = "Container port to expose"
  type        = number
  default     = 8080
}

variable "command" {
  description = "Container entrypoint command (optional)"
  type        = list(string)
  default     = []
}

variable "args" {
  description = "Container args (optional)"
  type        = list(string)
  default     = []
}

variable "service_account_email" {
  description = "Service account email for the runtime (optional)"
  type        = string
  default     = null
}

variable "min_scale" {
  description = "Minimum number of instances (autoscaling.knative.dev/minScale)"
  type        = number
  default     = null
}

variable "max_scale" {
  description = "Maximum number of instances (autoscaling.knative.dev/maxScale)"
  type        = number
  default     = null
}

variable "container_concurrency" {
  description = "Container concurrency (requests per instance)"
  type        = number
  default     = null
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = null
}

variable "ingress" {
  description = "Ingress setting: all or internal-and-cloud-load-balancing"
  type        = string
  default     = null
}


