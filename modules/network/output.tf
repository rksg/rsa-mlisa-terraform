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

output "global_addresses" {
  description = "Map of created global addresses"
  value       = google_compute_global_address.private_ip_blocks
}

output "service_networking_connection" {
  description = "The service networking connection"
  value       = google_service_networking_connection.private_vpc_connection
}
