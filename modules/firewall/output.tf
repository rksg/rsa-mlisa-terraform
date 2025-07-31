output "firewall_rule_name" {
  description = "Firewall rule name"
  value       = google_compute_firewall.firewall_rule.name
}