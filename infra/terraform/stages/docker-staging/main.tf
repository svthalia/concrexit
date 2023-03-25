terraform {
  required_version = ">=0.14.10"

  required_providers {
    aws = ">= 3.28.0"
  }

  backend "s3" {
    bucket  = "thalia-terraform-state"
    key     = "concrexit/docker-staging.tfstate"
    region  = "eu-west-1"
    profile = "thalia"
  }
}

module "concrexit" {
  source                = "../../concrexit"
  aws_profile           = "thalia"
  customer              = "thalia"
  stage                 = "docker-staging"
  zone_name             = "thalia.nu"
  domain                = "docker-staging.thalia.nu"
  ssh_public_key        = file("ssh-public-key.pub")
  cloudfront_public_key = file("cloudfront-public-key.pem")
  ec2_instance_type     = "t3a.micro"
}
