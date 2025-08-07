variable "project" {
  description = "The ID of the project to create the bucket in"
  type        = string
}

variable "bucket_name" {
  description = "The name of the bucket"
  type        = string
}

variable "location" {
  description = "The location of the bucket"
  type        = string
}

variable "storage_class" {
  description = "The storage class of the bucket"
  type        = string
  default     = "STANDARD"
}

variable "versioning_enabled" {
  description = "Whether versioning is enabled for the bucket"
  type        = bool
  default     = false
}

variable "uniform_bucket_level_access_enabled" {
  description = "Whether uniform bucket-level access is enabled"
  type        = bool
  default     = false
}

variable "public_access_prevention" {
  description = "The public access prevention setting"
  type        = string
  default     = "inherited"
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules for the bucket"
  type = list(object({
    action = object({
      type = string
    })
    condition = object({
        age = optional(number)
        matchesPrefix = optional(list(string))
    })
  }))
  default = null
}