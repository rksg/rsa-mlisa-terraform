variable "project" {
  description = "The ID of the project where the subnetwork will be created"
  type        = string
}

variable "region" {
  description = "The region where the subnetwork will be created"
  type        = string
}

variable "subnet_name" {
  description = "The name of the subnetwork"
  type        = string
}

variable "subnet_network" {
  description = "The name of the network this subnetwork belongs to"
  type        = string
}

variable "subnet_range_cidr" {
  description = "The IP address range that machines in this network will be assigned to"
  type        = string
}

variable "private_ip_google_access" {
  description = "Whether the VMs in this subnet can access Google services without assigned external IP addresses"
  type        = bool
  default     = false
}

variable "subnet_secondary_ip_ranges" {
  description = "An array of configurations for secondary IP ranges for VM instances contained in this subnetwork"
  type = list(object({
    name    = string
    ip_cidr_range = string
  }))
  default = []
} 