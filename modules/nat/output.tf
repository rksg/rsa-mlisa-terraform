output "router_name" {
  description = "The name of the created router"
  value       = google_compute_router.router.name
}

output "router_id" {
  description = "The ID of the created router"
  value       = google_compute_router.router.id
}

output "nat_name" {
  description = "The name of the created NAT"
  value       = google_compute_router_nat.nat.name
}

