resource "google_vpc_access_connector" "connector" {
  name          = var.connector_name
  region        = var.region
  project       = var.project
  min_throughput = var.min_throughput
  max_throughput = var.max_throughput
  subnet {
    name = var.connector_subnet_name
  }
}