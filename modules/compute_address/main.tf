resource "google_compute_address" "address" {
  name         = var.address_name
  description  = var.description
  address_type = var.address_type
  subnetwork   = var.subnetwork
  network_tier = var.network_tier
  purpose      = var.purpose
  ip_version   = var.ip_version
  project      = var.project
  region       = var.region
} 