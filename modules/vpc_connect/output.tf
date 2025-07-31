output "connector_name" {
  description = "The name of the created VPC connector"
  value       = google_vpc_access_connector.connector.name
}