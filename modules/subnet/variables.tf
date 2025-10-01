variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Subnetwork name"
  type        = string
}

variable "region" {
  description = "Subnetwork region"
  type        = string
}

variable "ip_cidr_range" {
  description = "CIDR range for the subnet"
  type        = string
}

variable "network" {
  description = "Self link or name of the VPC network"
  type        = string
}

variable "private_ip_google_access" {
  description = "Enable Private Google Access"
  type        = bool
  default     = true
}

variable "purpose" {
  description = "SUBNETWORK purpose"
  type        = string
  default     = null
}

variable "secondary_ip_ranges" {
  description = "Secondary IP ranges (list of { range_name, ip_cidr_range })"
  type = list(object({
    range_name    = string
    ip_cidr_range = string
  }))
  default = []
}


