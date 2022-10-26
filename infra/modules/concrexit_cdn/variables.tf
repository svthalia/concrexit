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

variable "media_bucket_id" {
  description = "The id used by the media S3 bucket"
  type        = string
}

variable "zone_name" {
  description = "The route53 hosted zone to use"
  type        = string
}

variable "webdomain" {
  description = "The web domain that points to the cdn"
  type        = string
}

variable "cloudfront_public_key" {
    description = "AWS CloudFront public key"
    type        = string
}
