variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Router name"
  type        = string
}

variable "region" {
  description = "Region"
  type        = string
}

variable "network" {
  description = "VPC network name or self link"
  type        = string
}


