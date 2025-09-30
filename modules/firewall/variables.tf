variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Firewall rule name"
  type        = string
}

variable "network" {
  description = "Network name or self link"
  type        = string
}

variable "direction" {
  description = "INGRESS or EGRESS"
  type        = string
  default     = "INGRESS"
}

variable "priority" {
  description = "Priority for the rule"
  type        = number
  default     = 1000
}

variable "protocol" {
  description = "Allowed protocol (tcp/udp/icmp/all)"
  type        = string
  default     = "tcp"
}

variable "ports" {
  description = "List of allowed ports"
  type        = list(string)
  default     = ["22"]
}

variable "source_ranges" {
  description = "Source CIDR ranges"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "target_tags" {
  description = "Target instance tags"
  type        = list(string)
  default     = []
}


