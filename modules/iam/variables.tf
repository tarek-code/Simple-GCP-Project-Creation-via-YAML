variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "iam_type" {
  description = "Type of IAM resource: member, binding, policy, or audit_config"
  type        = string
  default     = "member"
  validation {
    condition     = contains(["member", "binding", "policy", "audit_config"], var.iam_type)
    error_message = "iam_type must be member, binding, policy, or audit_config."
  }
}

variable "role" {
  description = "IAM role to bind"
  type        = string
  default     = null
}

variable "member" {
  description = "IAM member (e.g., serviceAccount:foo@bar.iam.gserviceaccount.com)"
  type        = string
  default     = null
}

variable "members" {
  description = "IAM members list"
  type        = list(string)
  default     = []
}

variable "policy_data" {
  description = "IAM policy data (for policy type)"
  type        = string
  default     = null
}

variable "service" {
  description = "Service for audit config (e.g., allServices, compute.googleapis.com)"
  type        = string
  default     = null
}

variable "audit_log_configs" {
  description = "Audit log configurations"
  type = list(object({
    log_type         = string
    exempted_members = optional(list(string))
  }))
  default = []
}

variable "condition" {
  description = "IAM condition: { title, expression, description? }"
  type = object({
    title       = string
    expression  = string
    description = optional(string)
  })
  default = null
}
