resource "google_project" "project" {
  project_id      = var.project_id
  name            = var.project_id
  org_id          = var.organization_id
  billing_account = var.billing_account
  labels          = var.labels
}

# Enable APIs
resource "google_project_service" "enabled_apis" {
  for_each = toset(var.apis)
  project  = google_project.project.project_id
  service  = each.value
}
