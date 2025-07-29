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
      log_config                         = object({
        enable = bool
        filter = string
      })
    })
  }))
  default = {}
}
