variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "role" {
  description = "IAM role to bind"
  type        = string
}

variable "member" {
  description = "IAM member (e.g., serviceAccount:foo@bar.iam.gserviceaccount.com)"
  type        = string
}


