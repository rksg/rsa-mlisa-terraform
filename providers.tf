terraform {

  #Specifies version requirements for Terraform CLI
  required_version = ">=1.10"
  
  #Specifies version requirements for google and google-beta providers
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.44.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.44.0"
    }
  }
  
}

provider "google" {
  project = var.project
  region  = var.region
}

provider "google-beta" {
  project = var.project
  region  = var.region
}