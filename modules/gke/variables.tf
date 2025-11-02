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

variable "network" {
  description = "VPC network name or self link"
  type        = string
  default     = null
}

variable "subnetwork" {
  description = "Subnetwork name or self link"
  type        = string
  default     = null
}

variable "enable_private_nodes" {
  description = "Enable private nodes"
  type        = bool
  default     = false
}

variable "master_ipv4_cidr_block" {
  description = "Master CIDR for private cluster"
  type        = string
  default     = null
}

variable "enable_network_policy" {
  description = "Enable network policy"
  type        = bool
  default     = false
}

variable "cluster_secondary_range_name" {
  description = "Secondary range name for pods"
  type        = string
  default     = null
}

variable "services_secondary_range_name" {
  description = "Secondary range name for services"
  type        = string
  default     = null
}

variable "node_auto_scaling" {
  description = "Node autoscaling for node pool: { min_node_count, max_node_count }"
  type = object({
    min_node_count = number
    max_node_count = number
  })
  default = null
}

variable "node_labels" {
  description = "Additional node labels"
  type        = map(string)
  default     = {}
}

variable "node_taints" {
  description = "Node taints list of { key, value, effect }"
  type = list(object({
    key    = string
    value  = string
    effect = string
  }))
  default = []
}


