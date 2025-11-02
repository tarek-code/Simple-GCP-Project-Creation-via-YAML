resource "google_service_account" "sa" {
  project                      = var.project_id
  account_id                   = var.account_id
  display_name                 = var.display_name
  description                  = var.description
  disabled                     = var.disabled
  create_ignore_already_exists = var.create_ignore_already_exists
}

# Assign IAM roles to the service account
resource "google_project_iam_member" "sa_roles" {
  for_each = toset(var.roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.sa.email}"
}

# Create service account key
resource "google_service_account_key" "sa_key" {
  count = var.create_key ? 1 : 0

  service_account_id = google_service_account.sa.name
  key_algorithm      = var.key_algorithm
  public_key_type    = var.public_key_type
  private_key_type   = var.private_key_type
}

# Save key to file if path is provided
resource "local_file" "sa_key_file" {
  count = var.create_key && var.key_file_path != null ? 1 : 0

  content  = base64decode(google_service_account_key.sa_key[0].private_key)
  filename = var.key_file_path
}


