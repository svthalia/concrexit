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

variable "deploy_dir" {
  description = "Directory outside of the repository to place deployment files"
  type        = string
}
