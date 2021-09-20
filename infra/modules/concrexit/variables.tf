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
