resource "google_cloudfunctions_function" "function" {
  name                  = var.function_name
  description           = var.description
  runtime               = var.runtime
  available_memory_mb   = var.available_memory_mb
  source_archive_bucket = var.source_archive_bucket
  source_archive_object = var.source_archive_object
  timeout               = var.timeout
  entry_point           = var.entry_point
  region                = var.region
  project               = var.project
  
  trigger_http = var.trigger_http
  
  vpc_connector = var.vpc_connector != "" ? var.vpc_connector : null
  vpc_connector_egress_settings = var.vpc_connector_egress_settings != "" ? var.vpc_connector_egress_settings : null
  
  environment_variables = var.environment_variables
  
  min_instances = var.min_instances
  max_instances = var.max_instances
} 