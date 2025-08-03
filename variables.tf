variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
}

variable "compute_network" {
  description = "Compute network configuration"
  type = object({
    name = string
  })
}

variable "nat_routers" {
  description = "Map of NAT routers"
  type = map(object({
    name        = string
    description = string
    network     = string
    nat         = object({
      name                               = string
      nat_ip_allocate_option             = string
      source_subnetwork_ip_ranges_to_nat = string
      max_ports_per_vm                   = number
      log_config                         = object({
        enable = bool
        filter = string
      })
    })
  }))
  default = {}
}

variable "compute_subnetworks" {
  description = "Compute subnetworks configuration"
  type = list(object(
    {
      name                      = string
      description               = string
      network                   = string
      ip_cidr_range             = string
      gateway_address           = string
      private_ip_google_access  = bool
      secondary_ip_range        = list(object(
        {
          name          = string
          ip_cidr_range = string
        }
      ))
    }
  ))
}

variable "vpc_access_connectors" {
  description = "List of VPC access connectors"
  type = list(object({
    name          = string
    description   = string
    network       = string
    ip_cidr_range = string
  }))
  default = []
}

variable "vpc_peer_global_addresses" {
  description = "List of VPC peer global addresses"
  type = list(object({
    name          = string
    description   = string
    network       = string
    address_type  = string
    address       = string
    prefix_length = number
    purpose       = string
  }))
  default = []
}

variable "dataproc_cluster" {
  description = "DataProc cluster configuration"
  type = object({
    cluster_name = string
    labels       = map(string)
    cluster_config = object({
      gce_cluster_config = object({
        internal_ip_only = bool
        subnetwork       = string
        tags             = list(string)
      })
      master_config = object({
        num_instances    = number
        machine_type     = string
        image            = string
        preemptibility   = string
        disk_config = object({
          boot_disk_size_gb = number
          boot_disk_type    = string
        })
      })
      worker_config = object({
        num_instances    = number
        machine_type     = string
        image            = string
        preemptibility   = string
        disk_config = object({
          boot_disk_size_gb = number
          boot_disk_type    = string
        })
      })
      software_config = object({
        image_version = string
        properties    = optional(map(string))
      })
    })
  })
  default = null
}


variable "firewall_rules" {
  description = "List of firewall rules"
  type = list(object({
    name                      = string
    description               = string
    network                   = string
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
  }))
  default = []
}

variable "cloud_run_services" {
  description = "List of Cloud Run services"
  type = list(object({
    name = string
    template = object({
      metadata = object({
        annotations = map(string)
      })
      spec = object({
        timeout_seconds      = number
        container_concurrency = number
        containers = list(object({
          image   = string
          command = list(string)
          args    = list(string)
          env = list(object({
            name  = string
            value = string
          }))
          resources = object({
            limits = object({
              cpu    = string
              memory = string
            })
          })
          ports = list(object({
            containerPort = number
            name         = string
          }))
        }))
      })
    })
    traffic = list(object({
      latestRevision = bool
      percent        = number
    }))
  }))
  default = []
}

variable "compute_addresses" {
  description = "List of compute addresses"
  type = list(object({
    name         = string
    description  = string
    address_type = string
    subnetwork   = string
    network_tier = string
    purpose      = string
    ip_version   = string
  }))
  default = []
}

variable "cloud_functions" {
  description = "List of Cloud Functions"
  type = list(object({
    name                  = string
    runtime               = string
    available_memory_mb   = number
    source_archive_bucket = string
    source_archive_object = string
    timeout               = number
    entry_point           = string
    trigger_http          = bool
    vpc_connector         = string
    vpc_connector_egress_settings = string
    environment_variables  = map(string)
    min_instances         = number
    max_instances         = number
  }))
  default = []
}

variable "container_clusters" {
  description = "List of GKE container clusters"
  type = list(object({
    name = string
    network = string
    subnetwork = string
    default_max_pods_per_node = string
    ip_allocation_policy = object({
      cluster_secondary_range_name  = string
      services_secondary_range_name = string
    })
    logging_service = string
    monitoring_service = string
    private_cluster_config = object({
      enable_private_nodes    = bool
      master_ipv4_cidr_block = string
    })
    addons_config = object({
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
    database_encryption = object({
      state = string
    })
    cluster_autoscaling = object({
      autoscaling_profile = string
    })
    node_pools = list(object({
      name = string
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
  }))
  default = []
}