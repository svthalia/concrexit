variable "tags" {
  description = "AWS tags for resources"
  type        = map(string)
}

variable "stage" {
  description = "Deployment stage for resource names"
  type        = string
}

variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
}
