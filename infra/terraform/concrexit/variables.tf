variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
}

variable "stage" {
  description = "The deployment stage"
  type        = string
}

variable "zone_name" {
  description = "The route53 hosted zone to use"
  type        = string
}

variable "domain" {
  description = "Domain name used to host the application in this stage"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key to use to SSH into the EC2 instance"
  type        = string
}

variable "cloudfront_public_key" {
  description = "AWS CloudFront public key"
  type        = string
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3a.small"
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
  default     = "thalia"
}
