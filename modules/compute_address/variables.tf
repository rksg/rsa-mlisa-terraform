variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region for the compute address"
  type        = string
}

variable "address_name" {
  description = "The name of the compute address"
  type        = string
}

variable "description" {
  description = "The description of the compute address"
  type        = string
  default     = ""
}

variable "address_type" {
  description = "The type of the address (INTERNAL or EXTERNAL)"
  type        = string
}

variable "subnetwork" {
  description = "The subnetwork for the compute address"
  type        = string
}

variable "network_tier" {
  description = "The network tier for the compute address"
  type        = string
}

variable "purpose" {
  description = "The purpose of the compute address"
  type        = string
}

variable "ip_version" {
  description = "The IP version for the compute address"
  type        = string
  default     = ""
} 