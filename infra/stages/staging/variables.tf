variable "stage" {
  description = "Deployment stage"
  type        = string
}

variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
}

variable "domain_name" {
  description = "Domain name used to host the application in this stage"
  type        = string
}

variable "aws_profile" {
  description = "AWS credentials profile to use"
  type        = string
}

variable "aws_region" {
  description = "AWS region where the application should be hosted"
  type        = string
}

variable "aws_tags" {
  description = "AWS tags that should be part of every resource for identification and billing"
  type        = map(string)
}

variable "ssh_private_key" {
  description = "The private key used to create the EC2 instance and connect to, public key is used in the Nix OS configuration"
  type        = string
}

variable "ssh_public_key" {
  description = "The public key used to create the EC2 instance, also used in the Nix OS configuration"
  type        = string
}
