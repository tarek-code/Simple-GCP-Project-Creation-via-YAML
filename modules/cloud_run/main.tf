resource "google_cloud_run_service" "service" {
  name     = var.name
  project  = var.project_id
  location = var.location

  template {
    metadata {
      annotations = merge(
        {},
        var.vpc_connector == null ? {} : {
          "run.googleapis.com/vpc-access-connector" = var.vpc_connector
          "run.googleapis.com/vpc-access-egress"    = coalesce(var.egress, "ALL_TRAFFIC")
        }
      )
    }
    spec {
      containers {
        image = var.image
        ports {
          name           = "http1"
          container_port = 8080
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


