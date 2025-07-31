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

variable "vpc_peer_global_addresses" {
  description = "List of VPC peer global addresses"
  type = list(object({
    name          = string
    description   = string
    address_type  = string
    purpose       = string
    prefix_length = number
    network       = string
    address       = string
  }))
  default = []
}