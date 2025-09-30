resource "google_dns_managed_zone" "zone" {
  project     = var.project_id
  name        = var.name
  dns_name    = var.dns_name
  description = var.description
}


