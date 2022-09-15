variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
  default     = "thalia"
}

variable "domain_name" {
  description = "Domain name used to host the application in this stage"
  type        = string
  default     = "thalia.nu"
}

variable "aws_profile" {
  description = "AWS credentials profile to use"
  type        = string
  default     = "thalia"
}

variable "aws_region" {
  description = "AWS region where the application should be hosted"
  type        = string
  default     = "eu-west-1"
}
