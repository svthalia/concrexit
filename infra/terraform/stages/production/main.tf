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
  source                   = "../../concrexit"
  aws_profile              = "thalia"
  customer                 = "thalia"
  stage                    = "production"
  zone_name                = "thalia.nu"
  domain                   = "thalia.nu"
  ssh_public_key           = file("ssh-public-key.pub")
  cloudfront_public_key    = file("cloudfront-public-key.pem")
  ec2_instance_type        = "t3a.small"
  facedetection_lambda_arn = "arn:aws:lambda:eu-west-1:627002765486:function:concrexit-facedetection-lambda:production"
}
