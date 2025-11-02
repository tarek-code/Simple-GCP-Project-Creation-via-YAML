variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Pub/Sub topic name"
  type        = string
}

variable "labels" {
  description = "Labels for the topic"
  type        = map(string)
  default     = {}
}

variable "subscriptions" {
  description = "List of subscriptions to create on this topic"
  type = list(object({
    name                       = string
    ack_deadline_seconds       = optional(number)
    retain_acked_messages      = optional(bool)
    message_retention_duration = optional(string)
    filter                     = optional(string)
    dead_letter_topic          = optional(string)
    max_delivery_attempts      = optional(number)
    push_endpoint              = optional(string)
    oidc_service_account_email = optional(string)
    oidc_audience              = optional(string)
    expiration_policy_ttl      = optional(string)
    retry_min_backoff          = optional(string)
    retry_max_backoff          = optional(string)
  }))
  default = []
}


