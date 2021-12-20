variable "tags" {
  description = "AWS tags for resources"
  type        = map(string)
}

variable "stage" {
  description = "The deployment stage"
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

variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
}

variable "hostname" {
  description = "The machine hostname, will also be used as EHLO name when sending emails"
  type        = string
}

variable "hostdomain" {
  description = "Domain used in the machine hostname"
  type        = string
}

variable "webdomain" {
  description = "The domain web requests for concrexit should go to. Letsencrypt certifcates are requested for this. This dns name should point to the created instance"
  type        = string
}

variable "gsuite_domain" {
  description = "The GSUITE_DOMAIN used for member sync"
  type        = string
  default     = null
}

variable "gsuite_members_domain" {
  description = "The GSUITE_MEMBERS_DOMAIN used for member sync"
  type        = string
  default     = null
}

variable "django_env" {
  description = "DJANGO_ENV for settings.py"
  type = string
}
