variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "VPC Connector name"
  type        = string
}

variable "region" {
  description = "Region for the connector"
  type        = string
}

variable "network" {
  description = "VPC network name"
  type        = string
}

variable "ip_cidr_range" {
  description = "CIDR range for connector (e.g., 10.8.0.0/28)"
  type        = string
}


