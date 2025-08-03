resource "google_container_node_pool" "node_pools" {
  for_each = { for idx, pool in var.node_pools : pool.name => pool }
  
  name       = each.value.name
  location   = var.region
  cluster    = google_container_cluster.cluster.name
  project    = var.project

  dynamic "autoscaling" {
    for_each = each.value.autoscaling !=null && each.value.autoscaling.enabled == true ? [each.value.autoscaling] : []
    content {
      total_min_node_count = autoscaling.value.total_min_node_count
      total_max_node_count = autoscaling.value.total_max_node_count
      max_node_count      = autoscaling.value.max_node_count
      min_node_count      = autoscaling.value.min_node_count
      location_policy     = autoscaling.value.location_policy
    }
  }

  management {
    auto_repair = each.value.management.auto_repair
    auto_upgrade = "false"
  }

  upgrade_settings {
    max_surge = each.value.upgrade_settings.max_surge
  }

  node_config {
    machine_type = each.value.node_config.machine_type
    disk_size_gb = each.value.node_config.disk_size_gb
    disk_type    = each.value.node_config.disk_type
    image_type   = each.value.node_config.image_type
    labels       = each.value.node_config.labels
    service_account = each.value.node_config.service_account
    oauth_scopes    = each.value.node_config.oauth_scopes

    shielded_instance_config {
      enable_integrity_monitoring = each.value.node_config.shielded_instance_config.enableIntegrityMonitoring
    }

    metadata = each.value.node_config.metadata

    dynamic "linux_node_config" {
      for_each = each.value.node_config.linux_node_config != null ? [each.value.node_config.linux_node_config] : []
      content {
        cgroup_mode = linux_node_config.value.cgroupMode
        sysctls = {}
      }
    }
  }
} 