resource "google_compute_firewall" "firewall_rule" {
  
  name          = var.firewall_rule.name
  description   = var.firewall_rule.description
  network       = var.firewall_rule.network
  priority      = var.firewall_rule.priority
  direction     = var.firewall_rule.direction
  disabled      = var.firewall_rule.disabled
  project       = var.project
  
  # Source and destination ranges
  source_ranges      = var.firewall_rule.source_ranges
  destination_ranges = var.firewall_rule.destination_ranges
  
  # Tags - only set if not empty
  source_tags = length(var.firewall_rule.source_tags) > 0 ? var.firewall_rule.source_tags : null
  target_tags = length(var.firewall_rule.target_tags) > 0 ? var.firewall_rule.target_tags : null
  
  # Service accounts - only set if not empty
  source_service_accounts = length(var.firewall_rule.source_service_accounts) > 0 ? var.firewall_rule.source_service_accounts : null
  target_service_accounts = length(var.firewall_rule.target_service_accounts) > 0 ? var.firewall_rule.target_service_accounts : null
  
  # Allowed rules
  dynamic "allow" {
    for_each = var.firewall_rule.allowed
    content {
      protocol = allow.value.ip_protocol
      ports    = allow.value.ports
    }
  }
  
  # Denied rules
  dynamic "deny" {
    for_each = var.firewall_rule.denied
    content {
      protocol = deny.value.ip_protocol
      ports    = deny.value.ports
    }
  }
}
