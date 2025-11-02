resource "google_compute_instance" "vm" {
  name                      = var.name
  project                   = var.project_id
  zone                      = var.zone
  machine_type              = var.machine_type
  description               = var.description
  tags                      = var.tags
  labels                    = var.labels
  metadata                  = var.metadata
  enable_display            = var.enable_display
  can_ip_forward            = var.can_ip_forward
  deletion_protection       = var.deletion_protection
  hostname                  = var.hostname
  allow_stopping_for_update = var.allow_stopping_for_update
  min_cpu_platform          = var.min_cpu_platform

  boot_disk {
    auto_delete = var.boot_disk_auto_delete
    initialize_params {
      image  = var.image
      labels = var.boot_disk_labels
      type   = var.boot_disk_type
      size   = var.boot_disk_size_gb
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork
    network_ip = var.network_ip
    dynamic "access_config" {
      for_each = var.assign_external_ip ? [1] : []
      content {
        network_tier = var.external_network_tier
      }
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

  dynamic "confidential_instance_config" {
    for_each = var.enable_confidential_compute ? [1] : []
    content {
      enable_confidential_compute = true
      confidential_instance_type  = var.confidential_instance_type
    }
  }

  dynamic "guest_accelerator" {
    for_each = var.guest_accelerators
    content {
      type  = guest_accelerator.value.type
      count = guest_accelerator.value.count
    }
  }

  dynamic "service_account" {
    for_each = var.service_account_email == null ? [] : [1]
    content {
      email  = var.service_account_email
      scopes = var.service_account_scopes
    }
  }

  dynamic "scheduling" {
    for_each = [1]
    content {
      preemptible         = var.scheduling_preemptible
      automatic_restart   = var.scheduling_automatic_restart
      on_host_maintenance = var.scheduling_on_host_maintenance
      provisioning_model  = var.scheduling_provisioning_model
    }
  }

  metadata_startup_script = var.metadata_startup_script

  dynamic "advanced_machine_features" {
    for_each = var.advanced_machine_features == null ? [] : [var.advanced_machine_features]
    content {
      threads_per_core   = try(advanced_machine_features.value.threads_per_core, null)
      visible_core_count = try(advanced_machine_features.value.visible_core_count, null)
      turbo_mode         = try(advanced_machine_features.value.turbo_mode, null)
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


