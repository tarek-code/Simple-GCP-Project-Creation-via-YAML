resource "google_secret_manager_secret" "secret" {
  project   = var.project_id
  secret_id = var.name
  dynamic "replication" {
    for_each = [1]
    content {
      dynamic "auto" {
        for_each = var.replication == null || try(var.replication.auto, false) == true ? [1] : []
        content {}
      }
      dynamic "user_managed" {
        for_each = var.replication != null && try(var.replication.user_managed, null) != null ? [1] : []
        content {
          dynamic "replicas" {
            for_each = var.replication.user_managed
            content {
              location = replicas.value.location
              dynamic "customer_managed_encryption" {
                for_each = try(replicas.value.kms_key_name, null) != null ? [1] : []
                content {
                  kms_key_name = replicas.value.kms_key_name
                }
              }
            }
          }
        }
      }
    }
  }
}

resource "google_secret_manager_secret_version" "version" {
  secret      = google_secret_manager_secret.secret.id
  secret_data = var.value
}

resource "google_secret_manager_secret_version" "extra" {
  for_each    = { for v in var.additional_versions : tostring(md5(v)) => v }
  secret      = google_secret_manager_secret.secret.id
  secret_data = each.value
}


