variable "project_id" {
  description = "Target GCP project ID"
  type        = string
}

variable "account_id" {
  description = "Service account ID (no domain)"
  type        = string
}

variable "display_name" {
  description = "Service account display name"
  type        = string
  default     = null
}

variable "description" {
  description = "Service account description"
  type        = string
  default     = null
}

variable "disabled" {
  description = "Whether a service account is disabled or not"
  type        = bool
  default     = false
}

variable "create_ignore_already_exists" {
  description = "If set to true, skip service account creation if a service account with the same email already exists"
  type        = bool
  default     = false
}

variable "roles" {
  description = "List of IAM roles to assign to the service account"
  type        = list(string)
  default     = []
}

variable "create_key" {
  description = "Whether to create a service account key"
  type        = bool
  default     = false
}

variable "key_algorithm" {
  description = "The algorithm used to generate the key"
  type        = string
  default     = "KEY_ALG_RSA_2048"
  validation {
    condition     = contains(["KEY_ALG_RSA_1024", "KEY_ALG_RSA_2048"], var.key_algorithm)
    error_message = "key_algorithm must be KEY_ALG_RSA_1024 or KEY_ALG_RSA_2048."
  }
}

variable "public_key_type" {
  description = "The output format of the public key"
  type        = string
  default     = "TYPE_X509_PEM_FILE"
  validation {
    condition     = contains(["TYPE_NONE", "TYPE_X509_PEM_FILE", "TYPE_RAW_PUBLIC_KEY"], var.public_key_type)
    error_message = "public_key_type must be TYPE_NONE, TYPE_X509_PEM_FILE, or TYPE_RAW_PUBLIC_KEY."
  }
}

variable "private_key_type" {
  description = "The output format of the private key"
  type        = string
  default     = "TYPE_GOOGLE_CREDENTIALS_FILE"
  validation {
    condition     = contains(["TYPE_UNSPECIFIED", "TYPE_PKCS12_FILE", "TYPE_GOOGLE_CREDENTIALS_FILE"], var.private_key_type)
    error_message = "private_key_type must be TYPE_UNSPECIFIED, TYPE_PKCS12_FILE, or TYPE_GOOGLE_CREDENTIALS_FILE."
  }
}

variable "key_file_path" {
  description = "Path to save the service account key file"
  type        = string
  default     = null
}


