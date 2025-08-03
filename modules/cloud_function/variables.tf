variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Function"
  type        = string
}

variable "function_name" {
  description = "The name of the Cloud Function"
  type        = string
}

variable "description" {
  description = "The description of the Cloud Function"
  type        = string
  default     = ""
}

variable "runtime" {
  description = "The runtime for the Cloud Function"
  type        = string
}

variable "available_memory_mb" {
  description = "Available memory in MB for the Cloud Function"
  type        = number
}

variable "source_archive_bucket" {
  description = "The GCS bucket containing the source archive"
  type        = string
}

variable "source_archive_object" {
  description = "The GCS object name of the source archive"
  type        = string
}

variable "timeout" {
  description = "The timeout for the Cloud Function (e.g., '540')"
  type        = number
}

variable "entry_point" {
  description = "The entry point for the Cloud Function"
  type        = string
}


variable "trigger_http" {
  description = "Whether the function is HTTP triggered"
  type        = bool
  default     = false
}

variable "vpc_connector" {
  description = "The VPC connector for the Cloud Function"
  type        = string
  default     = ""
}

variable "vpc_connector_egress_settings" {
  description = "The VPC connector egress settings"
  type        = string
  default     = ""
}

variable "environment_variables" {
  description = "Environment variables for the Cloud Function"
  type        = map(string)
  default     = {}
}

variable "min_instances" {
  description = "Minimum number of instances for the Cloud Function"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances for the Cloud Function"
  type        = number
  default     = 0
} 