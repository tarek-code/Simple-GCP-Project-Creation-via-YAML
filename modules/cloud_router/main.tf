resource "google_compute_router" "router" {
  name    = var.name
  project = var.project_id
  region  = var.region
  network = var.network

  dynamic "bgp" {
    for_each = var.asn == null ? [] : [1]
    content {
      asn = var.asn
      dynamic "advertised_ip_ranges" {
        for_each = var.bgp_advertised_ip_ranges
        content {
          range       = advertised_ip_ranges.value.range
          description = try(advertised_ip_ranges.value.description, null)
        }
      }
    }
  }
}

resource "google_compute_router_interface" "iface" {
  for_each   = { for i in var.interfaces : i.name => i }
  name       = each.value.name
  project    = var.project_id
  region     = var.region
  router     = google_compute_router.router.name
  ip_range   = each.value.ip_range
  subnetwork = each.value.subnetwork
}

resource "google_compute_router_peer" "peer" {
  for_each          = { for p in var.bgp_peers : p.name => p }
  name              = each.value.name
  project           = var.project_id
  region            = var.region
  router            = google_compute_router.router.name
  interface         = each.value.interface
  peer_asn          = each.value.peer_asn
  peer_ip_address   = each.value.peer_ip
  advertise_mode    = try(each.value.advertise_mode, null)
  advertised_groups = try(each.value.advertised_groups, null)

  dynamic "advertised_ip_ranges" {
    for_each = try(each.value.advertised_ip_ranges, [])
    content {
      range       = advertised_ip_ranges.value.range
      description = try(advertised_ip_ranges.value.description, null)
    }
  }
}


