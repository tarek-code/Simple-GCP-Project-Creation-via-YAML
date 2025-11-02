resource "google_cloudfunctions2_function" "function" {
  name        = var.name
  project     = var.project_id
  location    = var.location
  description = var.description

  build_config {
    runtime     = var.runtime
    entry_point = var.entry_point
    source {
      storage_source {
        bucket = var.source_bucket
        object = var.source_object
      }
    }
  }

  service_config {
    available_memory   = var.memory
    timeout_seconds    = var.timeout_seconds
    ingress_settings   = var.ingress_settings
    max_instance_count = var.max_instance_count
  }
}


