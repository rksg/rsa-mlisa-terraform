# Call the network module
module "network" {
  source = "./modules/network"
  
  # Use values from tfvars.json structure
  project         = var.project
  compute_network = var.compute_network.name
  region          = var.region
}

# Call the subnetwork module for each subnetwork
module "subnetworks" {
  source = "./modules/subnetwork"
  for_each = { for idx, subnet in var.compute_subnetworks : subnet.name => subnet }
  
  # Use values from tfvars.json structure
  project                    = var.project
  region                     = var.region
  subnet_name                = each.value.name
  subnet_network             = module.network.network_name
  subnet_range_cidr          = each.value.ip_cidr_range
  private_ip_google_access   = each.value.private_ip_google_access
  subnet_secondary_ip_ranges = each.value.secondary_ip_range
}

module "nat" {
    source = "./modules/nat"
    for_each = var.nat_routers

    # Use values from tfvars.json structure
    compute_network                     = module.network.network_name
    region                              = var.region
    nat_router_name                     = each.value.name
    nat_name                            = each.value.nat.name
    nat_ip_allocate_option              = each.value.nat.nat_ip_allocate_option
    source_subnetwork_ip_ranges_to_nat  = each.value.nat.source_subnetwork_ip_ranges_to_nat
    max_ports_per_vm                    = each.value.nat.max_ports_per_vm
    nat_log_config_enable               = each.value.nat.log_config.enable
    nat_log_config_filter               = each.value.nat.log_config.filter
}
