variable "zone_name" {
  description = "The route53 hosted zone to use"
  type        = string
}

variable "webdomain" {
  description = "The web domain that points to the concrexit instance"
  type        = string
}

variable "public_ipv4" {
  description = "The IPv4 address of the concrexit instance"
  type        = string
}

variable "public_ipv6" {
  description = "The IPv6 address of the concrexit instance"
  type        = string
}
