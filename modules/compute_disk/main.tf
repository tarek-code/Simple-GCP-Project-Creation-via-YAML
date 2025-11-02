resource "google_compute_disk" "disk" {
  project = var.project_id
  name    = var.name
  zone    = var.zone

  size     = var.size_gb
  type     = var.type
  image    = var.image
  snapshot = var.snapshot
  labels   = var.labels

  disk_encryption_key {
    kms_key_self_link = var.kms_key_self_link
  }
}

output "self_link" {
  value = google_compute_disk.disk.self_link
}

