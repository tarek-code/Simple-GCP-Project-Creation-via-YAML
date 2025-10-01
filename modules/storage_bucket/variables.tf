variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Bucket name"
  type        = string
}

variable "location" {
  description = "Bucket location (e.g., US, EU, us-central1)"
  type        = string
  default     = "US"
}

variable "uniform_bucket_level_access" {
  description = "Enable uniform bucket-level access"
  type        = bool
  default     = true
}

variable "enable_versioning" {
  description = "Enable object versioning"
  type        = bool
  default     = false
}

variable "labels" {
  description = "Labels for the bucket"
  type        = map(string)
  default     = {}
}

variable "force_destroy" {
  description = "Force destroy bucket even if not empty"
  type        = bool
  default     = false
}

variable "storage_class" {
  description = "Default storage class (e.g., STANDARD, NEARLINE, COLDLINE, ARCHIVE)"
  type        = string
  default     = null
}

variable "public_access_prevention" {
  description = "Public access prevention: enforced or inherited"
  type        = string
  default     = null
}

variable "default_kms_key_name" {
  description = "CMEK key for default encryption"
  type        = string
  default     = null
}

variable "logging" {
  description = "Logging config: { log_bucket, log_object_prefix }"
  type = object({
    log_bucket        = string
    log_object_prefix = optional(string)
  })
  default = null
}

variable "cors" {
  description = "CORS rules list"
  type = list(object({
    origin          = list(string)
    method          = list(string)
    response_header = optional(list(string))
    max_age_seconds = optional(number)
  }))
  default = []
}

variable "lifecycle_rules" {
  description = "Lifecycle rules list of { action { type, storage_class? }, condition {...} }"
  type = list(object({
    action = object({
      type          = string
      storage_class = optional(string)
    })
    condition = object({
      age                        = optional(number)
      created_before             = optional(string)
      with_state                 = optional(string)
      matches_storage_class      = optional(list(string))
      num_newer_versions         = optional(number)
      custom_time_before         = optional(string)
      days_since_custom_time     = optional(number)
      days_since_noncurrent_time = optional(number)
      noncurrent_time_before     = optional(string)
    })
  }))
  default = []
}

variable "retention_policy" {
  description = "Retention policy: { retention_period, is_locked? }"
  type = object({
    retention_period = number
    is_locked        = optional(bool)
  })
  default = null
}



