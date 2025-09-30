resource "google_pubsub_topic" "topic" {
  name    = var.name
  project = var.project_id
  labels  = var.labels
}


