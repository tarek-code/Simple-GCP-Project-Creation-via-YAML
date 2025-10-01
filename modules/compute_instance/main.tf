resource "google_compute_instance" "vm" {
  name         = var.name
  project      = var.project_id
  zone         = var.zone
  machine_type = var.machine_type
  tags         = var.tags
  metadata     = var.metadata

  boot_disk {
    initialize_params {
      image = var.image
    }
  }

  network_interface {
    subnetwork = var.subnetwork
    dynamic "access_config" {
      for_each = var.create_public_ip ? [1] : []
      content {}
    }
  }

  dynamic "attached_disk" {
    for_each = var.additional_disks
    content {
      device_name = each.value.name
      mode        = "READ_WRITE"
      source      = google_compute_disk.extra[each.key].self_link
    }
  }

  dynamic "shielded_instance_config" {
    for_each = var.enable_shielded_vm ? [1] : []
    content {
      enable_secure_boot          = var.shielded_secure_boot
      enable_vtpm                 = var.shielded_vtpm
      enable_integrity_monitoring = var.shielded_integrity_monitoring
    }
  }

  dynamic "service_account" {
    for_each = var.service_account_email == null ? [] : [1]
    content {
      email  = var.service_account_email
      scopes = var.service_account_scopes
    }
  }
}

resource "google_compute_disk" "extra" {
  for_each = { for d in var.additional_disks : d.name => d }
  name     = each.value.name
  project  = var.project_id
  zone     = var.zone
  type     = each.value.type
  size     = each.value.size_gb
}


