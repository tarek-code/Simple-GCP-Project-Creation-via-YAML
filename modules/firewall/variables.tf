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

variable "target_service_accounts" {
  description = "Target service accounts"
  type        = list(string)
  default     = []
}

variable "destination_ranges" {
  description = "Destination ranges (for EGRESS)"
  type        = list(string)
  default     = []
}

variable "allows" {
  description = "Multiple allow blocks: list of { protocol, ports }"
  type = list(object({
    protocol = string
    ports    = optional(list(string))
  }))
  default = []
}

variable "denies" {
  description = "Multiple deny blocks: list of { protocol, ports }"
  type = list(object({
    protocol = string
    ports    = optional(list(string))
  }))
  default = []
}

variable "source_tags" {
  description = "Source instance tags"
  type        = list(string)
  default     = []
}

variable "source_service_accounts" {
  description = "Source service accounts"
  type        = list(string)
  default     = []
}

variable "disabled" {
  description = "Whether the firewall rule is disabled"
  type        = bool
  default     = false
}

variable "description" {
  description = "Description of the firewall rule"
  type        = string
  default     = null
}

variable "enable_logging" {
  description = "Enable logging for this firewall rule"
  type        = bool
  default     = false
}

variable "log_config" {
  description = "Logging configuration"
  type = object({
    metadata = string
  })
  default = null
}


