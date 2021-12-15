terraform {
  required_version = ">=0.14.10"

  required_providers {
    aws = ">= 3.28.0"
  }

  backend "s3" {
    bucket  = "thalia-terraform-state"
    key     = "concrexit/staging.tfstate"
    region  = "eu-west-1"
    profile = "thalia"
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

module "concrexit" {
  source               = "../../modules/concrexit"
  stage                = "staging"
  tags                 = var.aws_tags
  customer             = var.customer
  webhostname          = "staging-tf"
  domain               = "thalia.nu"
  ssh_private_key      = var.ssh_private_key
  ssh_public_key       = var.ssh_public_key
}
