data "aws_s3_bucket" "media_bucket" {
  bucket = var.media_bucket_id
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

resource "aws_cloudfront_origin_access_control" "s3_access" {
  name                              = "${var.customer}-${var.stage}-concrexit-s3-access"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "this" {
  aliases = [var.webdomain]

  enabled          = true
  is_ipv6_enabled  = true
  price_class      = "PriceClass_100"
  retain_on_delete = false
  http_version     = "http3"

  origin {
    domain_name              = data.aws_s3_bucket.media_bucket.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_access.id
    origin_id                = "s3_bucket"
  }

  default_cache_behavior {
    target_origin_id       = "s3_bucket"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    trusted_key_groups = [aws_cloudfront_key_group.this.id]
    cache_policy_id    = data.aws_cloudfront_cache_policy.caching_optimized.id

  }

  ordered_cache_behavior {
    path_pattern           = "/public/*"
    target_origin_id       = "s3_bucket"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimized.id
  }

  viewer_certificate {
    acm_certificate_arn      = module.acm.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.1_2016"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
  })
}

data "aws_route53_zone" "primary" {
  name = var.zone_name
}

resource "aws_route53_record" "domain" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = var.webdomain
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.this.domain_name
    zone_id                = aws_cloudfront_distribution.this.hosted_zone_id
    evaluate_target_health = false
  }
}

# CloudFront requires a certificate to be imported in the us-east-1 region.
# See https://github.com/terraform-aws-modules/terraform-aws-acm/tree/v4.3.2#usage-with-cloudfront.
provider "aws" {
  profile = var.aws_profile
  alias   = "us-east-1"
  region  = "us-east-1"
}

module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "4.3.2"

  providers = {
    aws = aws.us-east-1
  }
  wait_for_validation = true

  domain_name = var.webdomain
  zone_id     = data.aws_route53_zone.primary.id

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
  })
}

resource "aws_cloudfront_key_group" "this" {
  name  = "${var.customer}-${var.stage}-concrexit-key-group"
  items = [aws_cloudfront_public_key.this.id]
}

resource "aws_cloudfront_public_key" "this" {
  name        = "${var.customer}-${var.stage}-concrexit-key"
  encoded_key = var.cloudfront_public_key
}

# Policy to allow CloudFront to access the S3 bucket.
# See https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html.
resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = data.aws_s3_bucket.media_bucket.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": {
    "Sid": "AllowCloudFrontServicePrincipalReadOnly",
    "Effect": "Allow",
    "Principal": {
      "Service": "cloudfront.amazonaws.com"
    },
    "Action": "s3:GetObject",
    "Resource": "${data.aws_s3_bucket.media_bucket.arn}/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "${aws_cloudfront_distribution.this.arn}"
      }
    }
  }
}
EOF
}
