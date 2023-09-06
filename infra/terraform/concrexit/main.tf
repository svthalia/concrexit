locals {
  tags = {
    Category    = "concrexit",
    Owner       = "technicie",
    Environment = var.stage,
    Terraform   = true
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = "eu-west-1"
}

module "network" {
  source   = "./modules/network"
  customer = var.customer
  stage    = var.stage
  tags     = local.tags
}

module "dns" {
  source      = "./modules/dns"
  zone_name   = var.zone_name
  webdomain   = var.domain
  public_ipv4 = module.network.public_ipv4
  public_ipv6 = module.network.public_ipv6
}

module "server" {
  source                   = "./modules/server"
  customer                 = var.customer
  stage                    = var.stage
  tags                     = local.tags
  depends_on               = [module.dns]
  aws_interface_id         = module.network.aws_interface_id
  ssh_public_key           = var.ssh_public_key
  ec2_instance_type        = var.ec2_instance_type
  facedetection_lambda_arn = var.facedetection_lambda_arn
}

module "cdn" {
  source                = "./modules/cdn"
  aws_profile           = var.aws_profile
  customer              = var.customer
  stage                 = var.stage
  tags                  = local.tags
  zone_name             = var.zone_name
  webdomain             = "cdn.${var.domain}"
  media_bucket_id       = module.server.media_bucket_id
  cloudfront_public_key = var.cloudfront_public_key
}
