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
}


