output "function_name" {
  description = "The name of the created Cloud Function"
  value       = google_cloudfunctions_function.function.name
}

output "function_url" {
  description = "The URL of the created Cloud Function"
  value       = google_cloudfunctions_function.function.https_trigger_url
} 