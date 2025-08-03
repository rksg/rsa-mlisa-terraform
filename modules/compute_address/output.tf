output "address_name" {
  description = "The name of the created compute address"
  value       = google_compute_address.address.name
}

output "gke_address" {
  description = "The IP address of the created compute address"
  value       = google_compute_address.address.address
} 