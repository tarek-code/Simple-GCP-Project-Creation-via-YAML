variable "project_id" {
  description = "The ID of the project to create"
  type        = string
}

variable "organization_id" {
  type    = string
  default = null
}

variable "billing_account" {
  description = "The billing account ID to link the project to"
  type        = string
}

variable "labels" {
  description = "A map of labels to assign to the project"
  type        = map(string)
  default     = {}
}

variable "apis" {
  description = "List of APIs to enable in the project"
  type        = list(string)
  default     = []
}

variable "create_project" {
  description = "Whether to create the project or use an existing one"
  type        = bool
  default     = true
}