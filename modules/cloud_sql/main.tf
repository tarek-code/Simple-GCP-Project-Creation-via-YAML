resource "google_sql_database_instance" "instance" {
  name                = var.name
  project             = var.project_id
  database_version    = var.database_version
  region              = var.region
  deletion_protection = var.deletion_protection

  settings {
    tier = var.tier

    disk_size = var.disk_size
    disk_type = var.disk_type

    ip_configuration {
      ipv4_enabled    = var.ipv4_enabled
      private_network = var.private_network
      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    dynamic "backup_configuration" {
      for_each = var.backup_configuration == null ? [] : [var.backup_configuration]
      content {
        enabled            = backup_configuration.value.enabled
        start_time         = try(backup_configuration.value.start_time, null)
        binary_log_enabled = try(backup_configuration.value.binary_log_enabled, null)
      }
    }

    dynamic "maintenance_window" {
      for_each = var.maintenance_window == null ? [] : [var.maintenance_window]
      content {
        day          = maintenance_window.value.day
        hour         = maintenance_window.value.hour
        update_track = try(maintenance_window.value.update_track, null)
      }
    }

    dynamic "database_flags" {
      for_each = var.database_flags
      content {
        name  = database_flags.value.name
        value = database_flags.value.value
      }
    }

    dynamic "insights_config" {
      for_each = var.insights_config == null ? [] : [var.insights_config]
      content {
        query_string_length     = try(insights_config.value.query_string_length, null)
        record_application_tags = try(insights_config.value.record_application_tags, null)
        record_client_address   = try(insights_config.value.record_client_address, null)
      }
    }
  }

  dynamic "encryption_key_name" {
    for_each = var.kms_key_name == null ? [] : [1]
    content  = var.kms_key_name
  }
}


