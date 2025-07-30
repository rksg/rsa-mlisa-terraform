variable "compute_network" {
  description = "The name of the compute network to create"
  type        = string
}

variable "region" {
  description = "The region where the router and NAT will be created"
  type        = string
}

variable "nat_router_name" {
  description = "The name of NAT router to be created"
  type        = string
}

variable "nat_name" {
  description = "The name of NAT router to be created"
  type        = string
}

variable "nat_ip_allocate_option" {
  description = "How external IPs should be allocated for the NAT"
  type        = string
  default     = "AUTO_ONLY"
  
  validation {
    condition     = contains(["AUTO_ONLY", "MANUAL_ONLY"], var.nat_ip_allocate_option)
    error_message = "nat_ip_allocate_option must be either 'AUTO_ONLY' or 'MANUAL_ONLY'."
  }
}

variable "source_subnetwork_ip_ranges_to_nat" {
  description = "How NAT should be configured for the subnetworks"
  type        = string
  default     = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  validation {
    condition     = contains(["ALL_SUBNETWORKS_ALL_IP_RANGES", "LIST_OF_SUBNETWORKS", "ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES"], var.source_subnetwork_ip_ranges_to_nat)
    error_message = "source_subnetwork_ip_ranges_to_nat must be one of: 'ALL_SUBNETWORKS_ALL_IP_RANGES', 'LIST_OF_SUBNETWORKS', 'ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES'."
  }
}

variable "max_ports_per_vm" {
  description = "Maximum number of ports allocated to a VM from the NAT external IP address pool"
  type        = number
  
  validation {
    condition     = var.max_ports_per_vm >= 1 && var.max_ports_per_vm <= 65536
    error_message = "max_ports_per_vm must be between 1 and 65536."
  }
}

variable "nat_log_config_enable" {
  description = "Whether to enable logging for the NAT"
  type        = bool
  default     = true
}

variable "nat_log_config_filter" {
  description = "What type of logs to collect for the NAT"
  type        = string
  default     = "ERRORS_ONLY"
  
  validation {
    condition     = contains(["ERRORS_ONLY", "TRANSLATIONS_ONLY", "ALL"], var.nat_log_config_filter)
    error_message = "nat_log_config_filter must be one of: 'ERRORS_ONLY', 'TRANSLATIONS_ONLY', 'ALL'."
  }
}
