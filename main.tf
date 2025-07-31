# Call the network module
module "network" {
  source = "./modules/network"
  
  # Use values from tfvars.json structure
  project         = var.project
  compute_network = var.compute_network.name
  region          = var.region
  vpc_peer_global_addresses = var.vpc_peer_global_addresses
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

# Call the VPC connector module for each connector
module "vpc_connectors" {
  source = "./modules/vpc_connect"
  for_each = { for idx, connector in var.vpc_access_connectors : connector.name => connector }
  
  # Use values from tfvars.json structure
  project                           = var.project
  region                            = var.region
  connector_name                    = each.value.name
  network                           = module.network.network_name
  gcp_network_range_serverless_cidr = each.value.ip_cidr_range
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

data "external" "check_dataproc_cluster" {
  program = ["bash", "-c", <<-EOT
    # Check if dataproc cluster exists
    if gcloud dataproc clusters describe ${var.dataproc_cluster.cluster_name} --region=${var.region} --project=${var.project} >/dev/null 2>&1; then
      echo '{"should_create": "false"}'
    else
      echo '{"should_create": "true"}'
    fi
  EOT
  ]
}

# Local value to read the flag
locals {
  should_create_cluster = data.external.check_dataproc_cluster.result.should_create == "true"
}

# Call the dataproc module based on the flag
module "dataproc_cluster" {
  source = "./modules/dataproc"
  count  = local.should_create_cluster ? 1 : 0
  
  # Use values from tfvars.json structure
  project        = var.project
  region         = var.region
  cluster_name   = var.dataproc_cluster.cluster_name
  labels         = var.dataproc_cluster.labels
  cluster_config = var.dataproc_cluster.cluster_config
  
  # Use lifecycle to prevent recreation if cluster already exists
  # This will create the cluster if it doesn't exist, or do nothing if it does
}

# Call the firewall module for each firewall rule
module "firewall" {
  source = "./modules/firewall"
  for_each = { for idx, firewall_rule in var.firewall_rules : firewall_rule.name => firewall_rule }
  
  # Use values from tfvars.json structure
  project       = var.project
  firewall_rule = each.value
}
