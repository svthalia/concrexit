terraform {
  required_version = ">=0.14.10"

  required_providers {
    aws = ">= 3.28.0"
  }

  backend "s3" {
    bucket  = "thalia-terraform-state"
    region  = "eu-west-1"
    profile = "thalia"
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

locals {
  tags = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "review",
    "ShaHash"     = var.sha_hash,
    "Terraform"   = true
  }
  webdomain = "${var.sha_hash}.${var.domain_name}"
}

data "aws_subnet" "review-subnet" {
  filter {
    name   = "tag:Name"
    values = ["${var.customer}-review-concrexit"]
  }
}

data "aws_security_group" "review-firewall" {
  filter {
    name   = "tag:Name"
    values = ["${var.customer}-review-concrexit"]
  }
}

resource "aws_network_interface" "concrexit-interface" {
  subnet_id       = data.aws_subnet.review-subnet.id
  security_groups = [data.aws_security_group.review-firewall.id]

  ipv6_address_count = 1

  tags = merge(local.tags, {
    Name = "${var.customer}-review-concrexit"
  })
}

module "concrexit" {
  source           = "../../modules/concrexit"
  stage            = "review-${var.sha_hash}"
  tags             = local.tags
  ssh_private_key  = var.ssh_private_key
  ssh_public_key   = var.ssh_public_key
  aws_interface_id = aws_network_interface.concrexit-interface.id
  public_ipv4      = null

  customer   = var.customer
  hostname   = var.sha_hash
  hostdomain = var.domain_name
  webdomain  = local.webdomain
  django_env = "development"
}

data "aws_route53_zone" "primary" {
  name = var.domain_name
}

resource "aws_route53_record" "www" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = local.webdomain
  type            = "A"
  ttl             = "300"
  records         = [module.concrexit.public_ipv4]
  allow_overwrite = true
}

resource "aws_route53_record" "www-ipv6" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = local.webdomain
  type            = "AAAA"
  ttl             = "300"
  records         = [module.concrexit.public_ipv6]
  allow_overwrite = true
}

resource "aws_route53_record" "wildcard" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = "*.${local.webdomain}"
  type            = "CNAME"
  ttl             = "300"
  records         = [local.webdomain]
  allow_overwrite = true
}
