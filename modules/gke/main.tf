resource "google_container_cluster" "cluster" {
  name     = var.name
  project  = var.project_id
  location = var.location

  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "pool" {
  project  = var.project_id
  cluster  = google_container_cluster.cluster.name
  location = var.location
  name     = var.node_pool_name

  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
    labels = var.labels
    tags   = var.tags
  }
}


