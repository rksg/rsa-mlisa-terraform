output "sql_instance_name" {
  description = "The name of the created PostgreSQL instance"
  value       = google_sql_database_instance.postgres.name
}

output "sql_instance_id" {
  description = "The ID of the created PostgreSQL instance"
  value       = google_sql_database_instance.postgres.id
}

output "sql_connection_name" {
  description = "The connection name of the PostgreSQL instance"
  value       = google_sql_database_instance.postgres.connection_name
}

output "sql_first_ip_address" {
  description = "The first IP address of the PostgreSQL instance"
  value       = google_sql_database_instance.postgres.first_ip_address
}

output "sql_private_ip_address" {
  description = "The private IP address of the PostgreSQL instance"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "sql_public_ip_address" {
  description = "The public IP address of the PostgreSQL instance"
  value       = google_sql_database_instance.postgres.public_ip_address
} 