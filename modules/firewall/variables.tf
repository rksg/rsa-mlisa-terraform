variable "project" {
  description = "The ID of the project where the firewall rules will be created"
  type        = string
}

variable "network" {
  description = "The name of associated VPC network"
  type        = string
}

variable "firewall_rule" {
  description = "Firewall rule to create"
  type = object({
    name                      = string
    description               = string
    priority                  = number
    direction                 = string
    disabled                  = bool
    source_ranges             = list(string)
    destination_ranges        = list(string)
    source_tags               = list(string)
    target_tags               = list(string)
    source_service_accounts   = list(string)
    target_service_accounts   = list(string)
    allowed = list(object({
      ip_protocol = string
      ports       = list(string)
    }))
    denied = list(object({
      ip_protocol = string
      ports       = list(string)
    }))
  })
} 