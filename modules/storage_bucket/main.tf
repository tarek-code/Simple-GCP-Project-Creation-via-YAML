resource "google_storage_bucket" "bucket" {
  name                        = var.name
  location                    = var.location
  project                     = var.project_id
  uniform_bucket_level_access = var.uniform_bucket_level_access

  labels = var.labels

  dynamic "versioning" {
    for_each = var.enable_versioning ? [1] : []
    content {
      enabled = true
    }
  }
}



