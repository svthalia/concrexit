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
  source     = "../../modules/concrexit"
  depends_on = [module.concrexit_dns]
  stage      = "staging"
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "staging",
    "Terraform"   = true
  }
  customer         = var.customer
  webhostname      = "staging"
  domain           = var.domain_name
  aws_interface_id = module.concrexit_network.aws_interface_id
  public_ipv4      = module.concrexit_network.public_ipv4
}

module "concrexit_network" {
  source = "../../modules/concrexit_network"
  stage  = "staging"
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "staging",
    "Terraform"   = true
  }
  customer = var.customer
}

module "concrexit_dns" {
  source      = "../../modules/concrexit_dns"
  zone_name   = var.domain_name
  webdomain   = "staging.${var.domain_name}"
  public_ipv4 = module.concrexit_network.public_ipv4
  public_ipv6 = module.concrexit_network.public_ipv6
}

module "concrexit_cdn" {
  source    = "../../modules/concrexit_cdn"
  zone_name = var.domain_name
  webdomain = "cdn.staging.${var.domain_name}"
  stage     = "staging"
  customer  = var.customer
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "staging",
    "Terraform"   = true
  }
  media_bucket_id = module.concrexit.media_bucket_id
}
