output "service_name" {
  description = "The name of the created Cloud Run service"
  value       = google_cloud_run_service.service.name
}

output "service_url" {
  description = "The URL of the created Cloud Run service"
  value       = google_cloud_run_service.service.status[0].url
} 