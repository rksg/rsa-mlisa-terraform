output "subnet_name" {
  description = "The name of the created subnetwork"
  value       = google_compute_subnetwork.subnet.name
}

output "subnet_id" {
  description = "The ID of the created subnetwork"
  value       = google_compute_subnetwork.subnet.id
}