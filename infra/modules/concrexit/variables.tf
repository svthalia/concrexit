variable "tags" {
  description = "AWS tags for resources"
  type        = map(string)
}

variable "stage" {
  description = "The deployment stage"
  type        = string
}

variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
}

variable "domain" {
  description = "The domain/route53 hosted zone to use"
  type        = string
}

variable "webhostname" {
  description = "The name to use on the hosted zone to receive web requests"
  type        = string
}

variable "aws_interface_id" {
  type = string
}

variable "public_ipv4" {
  type = string
}

variable "ssh_private_key" {
  type = string
}

variable "ssh_public_key" {
  type = string
}
