# Call the network module
module "network" {
  source = "./modules/network"
  
  # Use values from tfvars.json structure
  project         = var.project
  compute_network = var.compute_network.name
  region          = var.region
}

module "nat" {
    source = "./modules/nat"
    for_each = var.nat_routers

    # Use values from tfvars.json structure
    compute_network                     = each.value.network
    region                              = var.region
    nat_router_name                     = each.value.name
    nat_name                            = each.value.nat.name
    nat_ip_allocate_option              = each.value.nat.nat_ip_allocate_option
    source_subnetwork_ip_ranges_to_nat  = each.value.nat.source_subnetwork_ip_ranges_to_nat
    nat_log_config_enable               = each.value.nat.log_config.enable
    nat_log_config_filter               = each.value.nat.log_config.filter
}
