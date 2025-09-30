resource "google_compute_instance" "vm" {
  name         = var.name
  project      = var.project_id
  zone         = var.zone
  machine_type = var.machine_type
  tags         = var.tags

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
}


