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

variable "tags" {
  description = "AWS tags for resources"
  type        = map(string)
  default = {
    "Category"    = "concrexit",
    "Owner"       = "technicie",
    "Environment" = "review",
    "Terraform"   = true
  }
}

variable "stage" {
  description = "The deployment stage"
  type        = string
  default     = "review"
}

variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
  default     = "thalia"
}
