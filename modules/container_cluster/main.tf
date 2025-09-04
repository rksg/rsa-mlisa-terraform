resource "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.region
  project  = var.project

  network    = var.network
  subnetwork = var.subnetwork
  enable_shielded_nodes = false

  default_max_pods_per_node = var.default_max_pods_per_node

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  deletion_protection = var.deletion_protection
  
  ip_allocation_policy {
    cluster_secondary_range_name  = var.ip_allocation_policy.cluster_secondary_range_name
    services_secondary_range_name = var.ip_allocation_policy.services_secondary_range_name
  }

  logging_service    = var.logging_service
  monitoring_service = var.monitoring_service
  release_channel {
    channel = var.release_channel.channel
  }
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
  
  workload_identity_config {
    workload_pool = "${var.project}.svc.id.goog"
  }

  addons_config {
    network_policy_config {
      disabled = var.addons_config.network_policy_config.disabled
    }
    gce_persistent_disk_csi_driver_config {
      enabled = var.addons_config.gce_persistent_disk_csi_driver_config.enabled
    }
    gcs_fuse_csi_driver_config {
      enabled = var.addons_config.gcs_fuse_csi_driver_config.enabled
    }
  }
}