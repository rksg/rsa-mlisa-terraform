output "network_name" {
  description = "The name of the created compute network"
  value       = google_compute_network.network.name
}

output "network_self_link" {
  description = "The self-link of the created compute network"
  value       = google_compute_network.network.self_link
}

output "network_id" {
  description = "The ID of the created compute network"
  value       = google_compute_network.network.id
}
