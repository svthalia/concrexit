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

module "concrexit" {
  source = "../../modules/concrexit"
  depends_on = [
    aws_route53_record.www,
    aws_route53_record.wildcard
  ]
  stage = "staging"
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "staging",
    "Terraform"   = true
  }
  customer         = var.customer
  webhostname      = "staging"
  domain           = var.domain_name
  ssh_private_key  = var.ssh_private_key
  ssh_public_key   = var.ssh_public_key
  aws_interface_id = module.concrexit_network.aws_interface_id
  # We supply the ipv4 address to this module and get ipv6 address back
  # This weird construction is because only when creating the instance is the
  # ipv6 address known, but the elastic IP is created beforehand.
  public_ipv4      = module.concrexit_network.public_ipv4
}

data "aws_route53_zone" "primary" {
  name = var.domain_name
}

resource "aws_route53_record" "www" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = "staging.thalia.nu"
  type            = "A"
  ttl             = "300"
  records         = [module.concrexit_network.public_ipv4]
  allow_overwrite = true
}

resource "aws_route53_record" "www-ipv6" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = "staging.thalia.nu"
  type            = "AAAA"
  ttl             = "300"
  records         = [module.concrexit.public_ipv6]
  allow_overwrite = true
}

resource "aws_route53_record" "wildcard" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = "*.staging"
  type            = "CNAME"
  ttl             = "300"
  records         = ["staging.${var.domain_name}"]
  allow_overwrite = true
}
