variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "VPC network name"
  type        = string
}

variable "routing_mode" {
  description = "Global or REGIONAL routing"
  type        = string
  default     = "GLOBAL"
}

variable "description" {
  description = "Network description"
  type        = string
  default     = null
}


