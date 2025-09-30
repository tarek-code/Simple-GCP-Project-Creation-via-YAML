variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Cluster name"
  type        = string
}

variable "location" {
  description = "Region or zone"
  type        = string
  default     = "us-central1"
}

variable "node_pool_name" {
  description = "Node pool name"
  type        = string
  default     = "default-pool"
}

variable "node_count" {
  description = "Node count"
  type        = number
  default     = 1
}

variable "machine_type" {
  description = "Machine type"
  type        = string
  default     = "e2-standard-2"
}

variable "labels" {
  description = "Node labels"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Node tags"
  type        = list(string)
  default     = []
}


