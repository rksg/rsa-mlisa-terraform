terraform {

  #Specifies version requirements for Terraform CLI
  required_version = ">=1.10"
  
  #Specifies version requirements for google and google-beta providers
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.44.0"
    }
  }
  
  backend "gcs" {
    bucket  = "mlisa-dr-terraform-state"
    prefix  = "terraform/state"
  }
  
}

provider "google" {
  project = var.project
  region  = var.region
}