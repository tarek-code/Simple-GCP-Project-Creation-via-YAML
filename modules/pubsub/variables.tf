variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Pub/Sub topic name"
  type        = string
}

variable "labels" {
  description = "Labels for the topic"
  type        = map(string)
  default     = {}
}


