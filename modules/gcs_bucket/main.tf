resource "google_storage_bucket" "bucket" {
  name          = var.bucket_name
  location      = var.location
  force_destroy = false
  project       = var.project

  storage_class = var.storage_class

  versioning {
    enabled = var.versioning_enabled
  }

  uniform_bucket_level_access = var.uniform_bucket_level_access_enabled

  public_access_prevention = var.public_access_prevention

  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules != null ? var.lifecycle_rules : []
    content {
      action {
        type = lifecycle_rule.value.action.type
      }
      condition {
        age = lifecycle_rule.value.condition.age
        matches_prefix = lifecycle_rule.value.condition.matchesPrefix
      }
    }
  }
} 