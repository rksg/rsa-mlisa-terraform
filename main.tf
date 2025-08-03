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

# Call the Compute Address module for each address
module "compute_addresses" {
  source = "./modules/compute_address"
  for_each = { for idx, address in var.compute_addresses : address.name => address }
  
  # Use values from tfvars.json structure
  project       = var.project
  region        = var.region
  address_name  = each.value.name
  description   = each.value.description
  address_type  = each.value.address_type
  subnetwork    = each.value.subnetwork
  network_tier  = each.value.network_tier
  purpose       = each.value.purpose
  ip_version    = each.value.ip_version
}

# Local value to get the core internal LB address
locals {
  core_internal_lb_address = try(
    values({
      for k, v in module.compute_addresses : k => v.gke_address
      if can(regex(".*core-lb-internal-ip-address$", k))
    })[0],
    ""
  )
}

# Call the Cloud Run Services module for each service
module "cloud_run_services" {
  source = "./modules/cloud_run"
  for_each = { for idx, service in var.cloud_run_services : service.name => service }
  
  # Use values from tfvars.json structure
  project      = var.project
  region       = var.region
  service_name = each.value.name
  template     = each.value.template
  traffic      = each.value.traffic
  core_internal_ingress_ip = local.core_internal_lb_address
}

# Call the Cloud Functions module for each function
module "cloud_functions" {
  source = "./modules/cloud_function"
  for_each = { for idx, function in var.cloud_functions : function.name => function }
  
  # Use values from tfvars.json structure
  project                = var.project
  region                 = var.region
  function_name          = each.value.name
  runtime                = each.value.runtime
  available_memory_mb    = each.value.available_memory_mb
  source_archive_bucket  = each.value.source_archive_bucket
  source_archive_object  = each.value.source_archive_object
  timeout                = each.value.timeout
  entry_point            = each.value.entry_point
  trigger_http           = each.value.trigger_http
  vpc_connector          = each.value.vpc_connector
  vpc_connector_egress_settings = each.value.vpc_connector_egress_settings
  environment_variables  = each.value.environment_variables
  min_instances          = each.value.min_instances
  max_instances          = each.value.max_instances
}
