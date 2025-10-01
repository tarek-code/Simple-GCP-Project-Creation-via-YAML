variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Secret name"
  type        = string
}

variable "value" {
  description = "Secret value"
  type        = string
}

variable "replication" {
  description = "Replication config: auto {} or user_managed regions with optional kms key"
  type = object({
    auto = optional(bool)
    user_managed = optional(list(object({
      location     = string
      kms_key_name = optional(string)
    })))
  })
  default = null
}

variable "additional_versions" {
  description = "Optional additional secret versions: list of values"
  type        = list(string)
  default     = []
}


