resource "google_redis_instance" "redis" {
  name               = var.name
  project            = var.project_id
  region             = var.region
  tier               = var.tier
  memory_size_gb     = var.memory_size_gb
  redis_version      = var.redis_version
  display_name       = var.display_name
  connect_mode       = var.connect_mode
  authorized_network = var.authorized_network

  labels = var.labels

  dynamic "maintenance_policy" {
    for_each = var.maintenance_policy == null ? [] : [var.maintenance_policy]
    content {
      weekly_maintenance_window {
        day = maintenance_policy.value.day
        start_time {
          hours   = maintenance_policy.value.start_time.hours
          minutes = try(maintenance_policy.value.start_time.minutes, null)
          seconds = try(maintenance_policy.value.start_time.seconds, null)
          nanos   = try(maintenance_policy.value.start_time.nanos, null)
        }
      }
    }
  }

  dynamic "persistence_config" {
    for_each = var.persistence_config == null ? [] : [var.persistence_config]
    content {
      persistence_mode        = persistence_config.value.persistence_mode
      rdb_snapshot_period     = try(persistence_config.value.rdb_snapshot_period, null)
      rdb_snapshot_start_time = try(persistence_config.value.rdb_snapshot_start_time, null)
    }
  }
}


