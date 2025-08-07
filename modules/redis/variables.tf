variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "instance_name" {
  description = "The name of the Redis instance"
  type        = string
}

variable "display_name" {
  description = "The display name of the Redis instance"
  type        = string
}

variable "location_id" {
  description = "The location ID for the Redis instance"
  type        = string
}

variable "redis_version" {
  description = "The Redis version"
  type        = string
}

variable "tier" {
  description = "The service tier of the instance"
  type        = string
}

variable "memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
}


variable "authorized_network" {
  description = "The full name of the network that should be peered into Google Cloud"
  type        = string
}

variable "connect_mode" {
  description = "The connection mode of instance"
  type        = string
}

variable "auth_enabled" {
  description = "Indicates whether OSS Redis AUTH is enabled for the instance"
  type        = bool
}

variable "transit_encryption_mode" {
  description = "The TLS mode of the Redis instance"
  type        = string
}

variable "redis_configs" {
  description = "Redis configuration parameters"
  type        = map(string)
  default     = null
}

variable "replica_count" {
  description = "The number of replica nodes"
  type        = number
  default     = 0
}

variable "read_replicas_mode" {
  description = "Read replicas mode"
  type        = string
  default     = "READ_REPLICAS_DISABLED"
}

variable "persistence_config" {
  description = "Persistence configuration"
  type = object({
    persistence_mode      = string
  })
  default = null
} 