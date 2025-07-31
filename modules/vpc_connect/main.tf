resource "google_vpc_access_connector" "connector" {
  name          = var.connector_name
  network       = var.network
  region        = var.region
  project       = var.project
}