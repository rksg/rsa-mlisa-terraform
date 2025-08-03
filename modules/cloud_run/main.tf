resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region
  project  = var.project

  template {
    metadata {
      annotations = var.template.metadata.annotations
    }

    spec {
      timeout_seconds      = var.template.spec.timeout_seconds
      container_concurrency = var.template.spec.container_concurrency

      dynamic "containers" {
        for_each = var.template.spec.containers
        content {
          image   = containers.value.image
          command = containers.value.command
          args    = containers.value.args
          env {
            name  = "EXPORTER_URL"
            value = "http://${var.core_internal_ingress_ip}:5100"
          }
          env {
            name  = "PIVOT_PROXY_HOST"
            value = var.core_internal_ingress_ip
          }
          dynamic "env" {
            for_each = containers.value.env
            content {
              name  = env.value.name
              value = env.value.value
            }
          }

          dynamic "resources" {
            for_each = containers.value.resources != null ? [containers.value.resources] : []
            content {
              limits = resources.value.limits
            }
          }

          dynamic "ports" {
            for_each = containers.value.ports
            content {
              container_port = ports.value.containerPort
              name          = ports.value.name
            }
          }
        }
      }
    }
  }

  dynamic "traffic" {
    for_each = var.traffic
    content {
      latest_revision = traffic.value.latestRevision
      percent         = traffic.value.percent
    }
  }
} 