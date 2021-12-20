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
  ssh_private_key  = var.ssh_private_key
  ssh_public_key   = var.ssh_public_key
  aws_interface_id = module.concrexit_network.aws_interface_id
  public_ipv4      = module.concrexit_network.public_ipv4

  customer              = var.customer
  hostname              = "staging"
  hostdomain            = var.domain_name
  webdomain             = "staging.${var.domain_name}"
  gsuite_domain         = "staging.${var.domain_name}"
  gsuite_members_domain = "members.staging.${var.domain_name}"
  django_env            = "staging"
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
