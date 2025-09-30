variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Instance name"
  type        = string
}

variable "database_version" {
  description = "Database version (e.g., POSTGRES_14)"
  type        = string
  default     = "POSTGRES_14"
}

variable "region" {
  description = "Region for the instance"
  type        = string
  default     = "us-central1"
}

variable "tier" {
  description = "Machine type tier (e.g., db-f1-micro)"
  type        = string
  default     = "db-f1-micro"
}


