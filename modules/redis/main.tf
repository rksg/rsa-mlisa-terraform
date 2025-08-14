resource "google_redis_instance" "redis" {
  name           = var.instance_name
  display_name   = var.display_name
  region         = var.region
  redis_version  = var.redis_version
  tier           = var.tier
  memory_size_gb = var.memory_size_gb
  
  authorized_network = var.authorized_network
  connect_mode      = var.connect_mode
  
  auth_enabled             = var.auth_enabled
  transit_encryption_mode  = var.transit_encryption_mode
  
  redis_configs = var.redis_configs
  
  replica_count = var.replica_count
  read_replicas_mode = var.read_replicas_mode
  
  project = var.project

  persistence_config {
    persistence_mode = var.persistence_config.persistence_mode
  }
} 