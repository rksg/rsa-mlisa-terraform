variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region for the container cluster"
  type        = string
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
}

variable "network" {
  description = "The network for the GKE cluster"
  type        = string
}

variable "subnetwork" {
  description = "The subnetwork for the GKE cluster"
  type        = string
}

variable "default_max_pods_per_node" {
  description = "Default maximum pods per node"
  type        = string
}

variable "ip_allocation_policy" {
  description = "IP allocation policy for the cluster"
  type = object({
    cluster_secondary_range_name  = string
    services_secondary_range_name = string
  })
}

variable "logging_service" {
  description = "Logging service for the cluster"
  type        = string
}

variable "monitoring_service" {
  description = "Monitoring service for the cluster"
  type        = string
}

variable "private_cluster_config" {
  description = "Private cluster configuration"
  type = object({
    enable_private_nodes    = bool
    master_ipv4_cidr_block = string
  })
}

variable "release_channel" {
  type = object({
      channel = string
  })
}

variable "deletion_protection" {
  description = "Deletion protection flag for the GKE clsuter"
  type = bool
  default = true
}

variable "addons_config" {
  description = "Addons configuration for the cluster"
  type = object({
    kubernetes_dashboard = object({
      disabled = bool
    })
    network_policy_config = object({
      disabled = bool
    })
    gce_persistent_disk_csi_driver_config = object({
      enabled = bool
    })
    gcs_fuse_csi_driver_config = object({
      enabled = bool
    })
  })
}

variable "database_encryption" {
  description = "Database encryption configuration"
  type = object({
    state = string
  })
}

variable "cluster_autoscaling" {
  description = "Cluster autoscaling configuration"
  type = object({
    autoscaling_profile = string
  })
}

variable "node_pools" {
  description = "Node pools for the cluster"
  type = list(object({
    name = string
    initial_node_count = number
    autoscaling = object({
      enabled             = bool
      total_min_node_count = number
      total_max_node_count = number
      max_node_count      = number
      min_node_count      = number
      location_policy     = string
    })
    max_pods_constraint = object({
      max_pods_per_node = string
    })
    management = object({
      auto_repair = bool
    })
    upgrade_settings = object({
      max_surge = number
    })
    node_config = object({
      machine_type = string
      disk_size_gb = number
      disk_type    = string
      image_type   = string
      labels       = map(string)
      linux_node_config = map(string)
      service_account = string
      oauth_scopes    = list(string)
      shielded_instance_config = object({
        enableIntegrityMonitoring = bool
      })
      metadata = map(string)
    })
  }))
}