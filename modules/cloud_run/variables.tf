variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Run service"
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
}

variable "template" {
  description = "Template configuration for the Cloud Run service"
  type = object({
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
}

variable "traffic" {
  description = "Traffic configuration for the Cloud Run service"
  type = list(object({
    latestRevision = bool
    percent        = number
  }))
  default = []
}

variable "core_internal_ingress_ip" {
  description = "Value from GKE Cluster core Internal ingress IP"
  type        = string
}