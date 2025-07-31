variable "project" {
  description = "The ID of the project where the VPC connector will be created"
  type        = string
}

variable "region" {
  description = "The region where the VPC connector will be created"
  type        = string
}

variable "connector_name" {
  description = "The name of the subnetwork to create the VPC connector for"
  type        = string
}

variable "gcp_network_range_serverless_cidr" {
  description = "The IP address range for the VPC connector"
  type        = string
}

variable "network" {
  description = "The name of the network to create the VPC connector in"
  type        = string
}