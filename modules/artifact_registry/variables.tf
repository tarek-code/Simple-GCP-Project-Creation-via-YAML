variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "name" {
  description = "Repository name"
  type        = string
}

variable "location" {
  description = "Repository location"
  type        = string
  default     = "us"
}

variable "format" {
  description = "Repository format (DOCKER, MAVEN, NPM, etc.)"
  type        = string
  default     = "DOCKER"
}

variable "description" {
  description = "Repository description"
  type        = string
  default     = null
}


