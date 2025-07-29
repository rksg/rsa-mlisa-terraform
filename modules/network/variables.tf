variable "project" {
  description = "The ID of the project where the network will be created"
  type        = string
}

variable "compute_network" {
  description = "The name of the compute network to create"
  type        = string
}

variable "region" {
  description = "The region where the router and NAT will be created"
  type        = string
}

variable "auto_create_subnetworks" {
  description = "Whether to automatically create subnetworks for the network"
  type        = bool
  default     = false
}