variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Cloud NAT name"
  type        = string
}

variable "region" {
  description = "Region"
  type        = string
}

variable "router" {
  description = "Cloud Router name"
  type        = string
}

variable "nat_ip_allocation" {
  description = "AUTO_ONLY or MANUAL_ONLY"
  type        = string
  default     = "AUTO_ONLY"
}

variable "source_subnetwork_ip_ranges_to_nat" {
  description = "ALL_SUBNETWORKS_ALL_IP_RANGES or LIST_OF_SUBNETWORKS"
  type        = string
  default     = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}


