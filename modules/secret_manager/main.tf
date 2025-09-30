resource "google_secret_manager_secret" "secret" {
  project   = var.project_id
  secret_id = var.name

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "version" {
  secret      = google_secret_manager_secret.secret.id
  secret_data = var.value
}


