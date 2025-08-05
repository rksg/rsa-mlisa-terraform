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

variable "min_throughput" {
  description = "Minimum throughout VPC connector"
  type        = number
}

variable "max_throughput" {
  description = "Maximum throughout VPC connector"
  type        = number
}

variable "connector_subnet_name" {
  description = "The name of the subnet network to create the VPC connector in"
  type        = string
}