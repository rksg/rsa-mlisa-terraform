output "sql_private_ip_address" {
  description = "Private IP address of the PostgreSQL instances"
  value       = google_sql_database_instance.postgres.private_ip_address
}