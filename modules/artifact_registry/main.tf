resource "google_artifact_registry_repository" "repo" {
  project       = var.project_id
  location      = var.location
  repository_id = var.name
  description   = var.description
  format        = var.format
}


