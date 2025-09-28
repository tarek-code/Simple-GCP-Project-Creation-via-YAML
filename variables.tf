variable "project_id" {
  description = "The ID of the project"
  type        = string
}

variable "organization_id" {
  description = "Organization ID"
  type        = string
}

variable "billing_account" {
  description = "Billing account ID"
  type        = string
}

variable "labels" {
  description = "Labels for the project"
  type        = map(string)
  default     = {}
}

variable "apis" {
  description = "List of APIs to enable"
  type        = list(string)
  default     = []
}

