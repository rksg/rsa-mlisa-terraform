variable "project" {
  description = "The ID of the project where the DataProc cluster will be created"
  type        = string
}

variable "region" {
  description = "The region where the DataProc cluster will be created"
  type        = string
}

variable "cluster_name" {
  description = "The name of the DataProc cluster"
  type        = string
}

variable "labels" {
  description = "Labels to apply to the DataProc cluster"
  type        = map(string)
  default     = {}
}

variable "cluster_config" {
  description = "Configuration for the DataProc cluster"
  type = object({
    gce_cluster_config = object({
      internal_ip_only = bool
      subnetwork       = string
      tags             = list(string)
    })
    master_config = object({
      num_instances    = number
      machine_type     = string
      preemptibility   = string
      disk_config = object({
        boot_disk_size_gb = number
        boot_disk_type    = string
      })
    })
    worker_config = object({
      num_instances    = number
      machine_type     = string
      preemptibility   = string
      disk_config = object({
        boot_disk_size_gb = number
        boot_disk_type    = string
      })
    })
    software_config = object({
      image_version = string
      properties    = map(string)
    })
  })
} 