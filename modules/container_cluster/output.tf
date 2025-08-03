output "cluster_name" {
  description = "The name of the created GKE cluster"
  value       = google_container_cluster.cluster.name
}

output "cluster_endpoint" {
  description = "The endpoint of the created GKE cluster"
  value       = google_container_cluster.cluster.endpoint
} 