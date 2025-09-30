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
    }
  }

  autogenerate_revision_name = true
}


