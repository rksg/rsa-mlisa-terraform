
resource "google_compute_network" "network" {
  name                    = var.compute_network
  auto_create_subnetworks = var.auto_create_subnetworks
  project                 = var.project
}

resource "google_compute_global_address" "private_ip_blocks" {
  for_each = { for idx, global_address in var.vpc_peer_global_addresses : global_address.name => global_address }

  name          = each.value.name
  purpose       = each.value.purpose
  address_type  = each.value.address_type
  address       = each.value.address
  prefix_length = each.value.prefix_length
  network       = google_compute_network.network.self_link
  description   = each.value.description
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.network.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [for private_ip_block in google_compute_global_address.private_ip_blocks : private_ip_block.name]
}