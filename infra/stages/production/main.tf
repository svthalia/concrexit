terraform {
  required_version = ">=0.14.10"

  required_providers {
    aws = ">= 3.28.0"
  }

  backend "s3" {
    bucket  = "thalia-terraform-state"
    key     = "concrexit/production.tfstate"
    region  = "eu-west-1"
    profile = "thalia"
  }
}

module "concrexit" {
  source               = "../../modules/concrexit"
  stage                = "production"
  tags                 = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "production",
    "Terraform"   = true
  }
  customer             = var.customer
  webhostname          = "production"
  domain               = var.domain_name
  ssh_private_key      = var.ssh_private_key
  ssh_public_key       = var.ssh_public_key
}
