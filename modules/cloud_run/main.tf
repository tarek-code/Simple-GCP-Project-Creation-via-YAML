resource "google_cloud_run_service" "service" {
  name     = var.name
  project  = var.project_id
  location = var.location

  template {
    metadata {
      annotations = merge(
        var.annotations,
        var.vpc_connector == null ? {} : {
          "run.googleapis.com/vpc-access-connector" = var.vpc_connector
          "run.googleapis.com/vpc-access-egress"    = coalesce(var.egress, "all")
        },
        var.min_scale == null ? {} : { "autoscaling.knative.dev/minScale" = tostring(var.min_scale) },
        var.max_scale == null ? {} : { "autoscaling.knative.dev/maxScale" = tostring(var.max_scale) },
        var.ingress == null ? {} : { "run.googleapis.com/ingress" = var.ingress }
      )
    }
    spec {
      service_account_name  = var.service_account_email
      container_concurrency = var.container_concurrency
      timeout_seconds       = var.timeout_seconds
      containers {
        image = var.image
        dynamic "env" {
          for_each = var.env
          content {
            name  = env.key
            value = env.value
          }
        }
        dynamic "ports" {
          for_each = [1]
          content {
            name           = "http1"
            container_port = var.container_port
          }
        }
        command = var.command
        args    = var.args
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


