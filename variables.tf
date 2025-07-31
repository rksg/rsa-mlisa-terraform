variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
}

variable "compute_network" {
  description = "Compute network configuration"
  type = object({
    name = string
  })
}

variable "nat_routers" {
  description = "Map of NAT routers"
  type = map(object({
    name        = string
    description = string
    network     = string
    nat         = object({
      name                               = string
      nat_ip_allocate_option             = string
      source_subnetwork_ip_ranges_to_nat = string
      max_ports_per_vm                   = number
      log_config                         = object({
        enable = bool
        filter = string
      })
    })
  }))
  default = {}
}

variable "compute_subnetworks" {
  description = "Compute subnetworks configuration"
  type = list(object(
    {
      name                      = string
      description               = string
      network                   = string
      ip_cidr_range             = string
      gateway_address           = string
      private_ip_google_access  = bool
      secondary_ip_range        = list(object(
        {
          name          = string
          ip_cidr_range = string
        }
      ))
    }
  ))
}

variable "vpc_access_connectors" {
  description = "List of VPC access connectors"
  type = list(object({
    name          = string
    description   = string
    network       = string
    ip_cidr_range = string
  }))
  default = []
}

variable "vpc_peer_global_addresses" {
  description = "List of VPC peer global addresses"
  type = list(object({
    name          = string
    description   = string
    network       = string
    address_type  = string
    address       = string
    prefix_length = number
    purpose       = string
  }))
  default = []
}