resource "google_compute_router" "router" {
  name    = var.nat_router_name
  network = var.compute_network
  region  = var.region
}

resource "google_compute_router_nat" "nat" {
  name                               = var.nat_name
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = var.nat_ip_allocate_option
  source_subnetwork_ip_ranges_to_nat = var.source_subnetwork_ip_ranges_to_nat

  log_config {
    enable = var.nat_log_config_enable
    filter = var.nat_log_config_filter
  }
}