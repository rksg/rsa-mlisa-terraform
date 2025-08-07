output "redis_instance_name" {
  description = "The name of the created Redis instance"
  value       = google_redis_instance.redis.name
}

output "redis_instance_id" {
  description = "The ID of the created Redis instance"
  value       = google_redis_instance.redis.id
}

output "redis_host" {
  description = "The IP address of the instance"
  value       = google_redis_instance.redis.host
}

output "redis_port" {
  description = "The port number of the instance"
  value       = google_redis_instance.redis.port
}

output "redis_current_location_id" {
  description = "The current zone where the Redis endpoint is placed"
  value       = google_redis_instance.redis.current_location_id
} 