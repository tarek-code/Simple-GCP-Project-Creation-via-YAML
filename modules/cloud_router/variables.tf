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

variable "asn" {
  description = "BGP ASN for the router"
  type        = number
  default     = null
}

variable "bgp_advertised_ip_ranges" {
  description = "List of BGP advertised ranges: list of { range, description? }"
  type = list(object({
    range       = string
    description = optional(string)
  }))
  default = []
}

variable "interfaces" {
  description = "Router interfaces (for HA VPN/attachments): list of { name, ip_range, subnetwork }"
  type = list(object({
    name       = string
    ip_range   = string
    subnetwork = string
  }))
  default = []
}

variable "bgp_peers" {
  description = "BGP peers list: { name, interface, peer_asn, peer_ip, advertise_mode?, advertised_groups?, advertised_ip_ranges? }"
  type = list(object({
    name              = string
    interface         = string
    peer_asn          = number
    peer_ip           = string
    advertise_mode    = optional(string)
    advertised_groups = optional(list(string))
    advertised_ip_ranges = optional(list(object({
      range       = string
      description = optional(string)
    })))
  }))
  default = []
}


