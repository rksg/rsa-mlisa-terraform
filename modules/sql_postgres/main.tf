resource "google_sql_database_instance" "postgres" {
  name             = var.instance_name
  database_version = var.database_version
  region           = var.region
  project          = var.project

  settings {
    tier                        = var.machine_type
    availability_type           = var.availability_type
    disk_size                   = var.data_disk_size_gb
    disk_type                   = var.data_disk_type
    disk_autoresize             = true
    deletion_protection_enabled = var.deletion_protection
    
    dynamic "database_flags" {
      for_each = var.database_flags != null ? var.database_flags : []
      content {
        name  = database_flags.value.name
        value = database_flags.value.value
      }
    }

    dynamic "backup_configuration" {
      for_each = var.backup_configuration != null ? [var.backup_configuration] : []
      content {
        enabled = backup_configuration.value.enabled
        binary_log_enabled =backup_configuration.value.binary_log_enabled
      }
    }

    dynamic "ip_configuration" {
      for_each = var.ip_configuration != null ? [var.ip_configuration] : []
      content {
        private_network = "projects/${var.project}/global/networks/${var.network}"
        ipv4_enabled =ip_configuration.value.ipv4_enabled
      }
    }
   
  }
  deletion_protection = var.deletion_protection
}

resource "google_sql_database" "database" {
  depends_on =[
    resource.google_sql_database_instance.postgres
  ]
  for_each = { for idx, database in var.databases : database => database }
  name     = each.value
  instance = var.instance_name
}

resource "google_sql_user" "users" {
  depends_on =[
    resource.google_sql_database_instance.postgres
  ]
  name     = var.database_user
  instance = var.instance_name
  password_wo = var.sql_postgres_password[var.database_user]
  lifecycle {
    ignore_changes = [password]
  }
}