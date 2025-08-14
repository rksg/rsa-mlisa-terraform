resource "google_dataproc_cluster" "dpc_cluster" {
  name                          = var.cluster_name
  region                        = var.region
  project                       = var.project
  graceful_decommission_timeout = "120s"
  labels                        = var.labels

  lifecycle {
    ignore_changes = [
      labels
    ]
    prevent_destroy = true
  }
  
  cluster_config {
    gce_cluster_config {
      internal_ip_only = var.cluster_config.gce_cluster_config.internal_ip_only
      subnetwork       = var.cluster_config.gce_cluster_config.subnetwork
      tags             = var.cluster_config.gce_cluster_config.tags
    }
    
    master_config {
      num_instances  = var.cluster_config.master_config.num_instances
      machine_type   = var.cluster_config.master_config.machine_type

      disk_config {
        boot_disk_size_gb = var.cluster_config.master_config.disk_config.boot_disk_size_gb
        boot_disk_type    = var.cluster_config.master_config.disk_config.boot_disk_type
      }
    }
    
    worker_config {
      num_instances  = var.cluster_config.worker_config.num_instances
      machine_type   = var.cluster_config.worker_config.machine_type
      
      disk_config {
        boot_disk_size_gb = var.cluster_config.worker_config.disk_config.boot_disk_size_gb
        boot_disk_type    = var.cluster_config.worker_config.disk_config.boot_disk_type
      }
    }
    
    software_config {
      image_version = var.cluster_config.software_config.image_version
      override_properties = var.cluster_config.software_config.properties
    }
  }
}