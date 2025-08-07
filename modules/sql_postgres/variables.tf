variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "instance_name" {
  description = "The name of the PostgreSQL instance"
  type        = string
}

variable "database_version" {
  description = "The PostgreSQL database version"
  type        = string
}

variable "region" {
  description = "The GCP region for the PostgreSQL instance"
  type        = string
}

variable "machine_type" {
  description = "The machine type for the PostgreSQL instance"
  type        = string
}

variable "availability_type" {
  description = "The availability type for the PostgreSQL instance"
  type        = string
  default     = "ZONAL"
}

variable "data_disk_size_gb" {
  description = "The size of the data disk in GB"
  type        = string
  default     = "10"
}

variable "data_disk_type" {
  description = "The type of the data disk"
  type        = string
  default     = "PD_SSD"
}

variable "database_flags" {
  description = "List of database flags for the PostgreSQL instance"
  type = list(object({
    name  = string
    value = string
  }))
  default = null
}

variable "backup_configuration" {
  description = "Backup configuration for the PostgreSQL instance"
  type = object({
    enabled = bool
    binary_log_enabled = bool
  })
  default = null
}

variable "ip_configuration" {
  description = "IP configuration for the PostgreSQL instance"
  type = object({
    private_network = string
    ipv4_enabled = bool
  })
}

variable "databases" {
  description = "List of databases for the PostgreSQL instance"
  type = list(string)
}