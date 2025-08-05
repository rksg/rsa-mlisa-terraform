resource "google_compute_subnetwork" "subnet" {
  ip_cidr_range              = var.subnet_range_cidr
  name                       = var.subnet_name
  description                = var.description
  network                    = var.subnet_network
  private_ip_google_access   = var.private_ip_google_access
  private_ipv6_google_access = "DISABLE_GOOGLE_ACCESS"
  project                    = var.project
  purpose                    = "PRIVATE"
  region                     = var.region
  
  dynamic "secondary_ip_range" {
    for_each = var.subnet_secondary_ip_ranges
    content {
        range_name    = secondary_ip_range.value.name
        ip_cidr_range = secondary_ip_range.value.ip_cidr_range
    }
  }
}