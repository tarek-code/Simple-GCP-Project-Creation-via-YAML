resource "google_project_iam_member" "binding" {
  project = var.project_id
  role    = var.role
  member  = var.member
}


