resource "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.region
  project  = var.project

  network    = var.network
  subnetwork = var.subnetwork
  enable_shielded_nodes = false

  default_max_pods_per_node = var.default_max_pods_per_node

  ip_allocation_policy {
    cluster_secondary_range_name  = var.ip_allocation_policy.cluster_secondary_range_name
    services_secondary_range_name = var.ip_allocation_policy.services_secondary_range_name
  }

  logging_service    = var.logging_service
  monitoring_service = var.monitoring_service

  private_cluster_config {
    enable_private_nodes    = var.private_cluster_config.enable_private_nodes
    master_ipv4_cidr_block = var.private_cluster_config.master_ipv4_cidr_block
  }

  database_encryption {
    state = var.database_encryption.state
  }

  cluster_autoscaling {
    autoscaling_profile = var.cluster_autoscaling.autoscaling_profile
  }
}