resource "google_container_cluster" "cluster" {
  name     = var.name
  project  = var.project_id
  location = var.location

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network
  subnetwork = var.subnetwork

  dynamic "ip_allocation_policy" {
    for_each = (var.cluster_secondary_range_name == null && var.services_secondary_range_name == null) ? [] : [1]
    content {
      cluster_secondary_range_name  = var.cluster_secondary_range_name
      services_secondary_range_name = var.services_secondary_range_name
    }
  }

  dynamic "private_cluster_config" {
    for_each = var.enable_private_nodes ? [1] : []
    content {
      enable_private_nodes    = true
      enable_private_endpoint = false
      master_ipv4_cidr_block  = var.master_ipv4_cidr_block
    }
  }

  dynamic "network_policy" {
    for_each = var.enable_network_policy ? [1] : []
    content {
      enabled  = true
      provider = "CALICO"
    }
  }
}

resource "google_container_node_pool" "pool" {
  project  = var.project_id
  cluster  = google_container_cluster.cluster.name
  location = var.location
  name     = var.node_pool_name

  node_count = var.node_count

  dynamic "autoscaling" {
    for_each = var.node_auto_scaling == null ? [] : [var.node_auto_scaling]
    content {
      min_node_count = autoscaling.value.min_node_count
      max_node_count = autoscaling.value.max_node_count
    }
  }

  node_config {
    machine_type = var.machine_type
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
    labels = merge(var.labels, var.node_labels)
    tags   = var.tags

    dynamic "taint" {
      for_each = var.node_taints
      content {
        key    = taint.value.key
        value  = taint.value.value
        effect = taint.value.effect
      }
    }
  }
}


