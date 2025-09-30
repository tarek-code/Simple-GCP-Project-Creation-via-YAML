resource "google_cloud_run_service" "service" {
  name     = var.name
  project  = var.project_id
  location = var.location

  template {
    spec {
      containers {
        image = var.image
        ports {
          name           = "http1"
          container_port = 8080
        }
      }
      dynamic "vpc_access" {
        for_each = var.vpc_connector == null ? [] : [1]
        content {
          connector = var.vpc_connector
          egress    = var.egress
        }
      }
    }
  }

  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "public_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.location
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}


