variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "dataset_id" {
  description = "BigQuery dataset id"
  type        = string
}

variable "location" {
  description = "Dataset location"
  type        = string
  default     = "US"
}

variable "labels" {
  description = "Dataset labels"
  type        = map(string)
  default     = {}
}


