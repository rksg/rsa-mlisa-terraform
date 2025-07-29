
resource "google_compute_network" "network" {
  name                    = var.compute_network
  auto_create_subnetworks = var.auto_create_subnetworks
  project                 = var.project
}