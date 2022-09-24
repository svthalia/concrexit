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

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

module "concrexit" {
  source = "../../modules/concrexit"
  stage  = "production"
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "production",
    "Terraform"   = true
  }
  customer         = var.customer
  webhostname      = "production"
  domain           = var.domain_name
  aws_interface_id = module.concrexit_network.aws_interface_id
  public_ipv4      = module.concrexit_network.public_ipv4
}

module "concrexit_network" {
  source = "../../modules/concrexit_network"
  stage  = "production"
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "production",
    "Terraform"   = true
  }
  customer = var.customer
}

module "concrexit_dns" {
  source      = "../../modules/concrexit_dns"
  zone_name   = var.domain_name
  webdomain   = "production.thalia.nu"
  public_ipv4 = module.concrexit_network.public_ipv4
  public_ipv6 = module.concrexit_network.public_ipv6
}

module "concrexit_cdn" {
  source    = "../../modules/concrexit_cdn"
  zone_name = var.domain_name
  webdomain = "cdn.${var.domain_name}"
  stage     = "production"
  customer  = var.customer
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "production",
    "Terraform"   = true
  }
  media_bucket_id = module.concrexit.media_bucket_id
}
