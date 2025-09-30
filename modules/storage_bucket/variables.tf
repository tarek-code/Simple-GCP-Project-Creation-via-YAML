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



