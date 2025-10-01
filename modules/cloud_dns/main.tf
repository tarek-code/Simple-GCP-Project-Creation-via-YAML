resource "google_dns_managed_zone" "zone" {
  project     = var.project_id
  name        = var.name
  dns_name    = var.dns_name
  description = var.description
}

resource "google_dns_record_set" "records" {
  for_each     = { for r in var.record_sets : "${r.name}_${r.type}" => r }
  project      = var.project_id
  managed_zone = google_dns_managed_zone.zone.name
  name         = each.value.name
  type         = each.value.type
  ttl          = each.value.ttl
  rrdatas      = each.value.rrdatas
}


