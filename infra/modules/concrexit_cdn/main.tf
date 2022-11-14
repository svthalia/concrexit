data "aws_s3_bucket" "media_bucket" {
  bucket = var.media_bucket_id
}

module "cloudfront" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "3.0.2"

  aliases = [var.webdomain]

  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_100"
  retain_on_delete    = false
  wait_for_deployment = false
  http_version        = "http3"

  default_root_object = "index.html"

  create_origin_access_identity = true
  origin_access_identities = {
    s3_bucket = "Access from the CloudFront distribution"
  }

  origin = {
    s3_bucket = {
      domain_name = data.aws_s3_bucket.media_bucket.bucket_regional_domain_name
      s3_origin_config = {
        origin_access_identity = "s3_bucket" # key in `origin_access_identities`
      }
    }
  }

  default_cache_behavior = {
    path_pattern           = "*"
    target_origin_id       = "s3_bucket"
    viewer_protocol_policy = "redirect-to-https"
    trusted_key_groups     = [aws_cloudfront_key_group.this.id]

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true
    query_string    = true
  }

  viewer_certificate = {
    acm_certificate_arn      = module.acm.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.1_2016"
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
    name                   = module.cloudfront.cloudfront_distribution_domain_name
    zone_id                = module.cloudfront.cloudfront_distribution_hosted_zone_id
    evaluate_target_health = false
  }
}

provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}

module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "4.1.1"

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

data "aws_iam_policy_document" "s3_policy" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${data.aws_s3_bucket.media_bucket.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = module.cloudfront.cloudfront_origin_access_identity_iam_arns
    }
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [data.aws_s3_bucket.media_bucket.arn]

    principals {
      type        = "AWS"
      identifiers = module.cloudfront.cloudfront_origin_access_identity_iam_arns
    }
  }
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = data.aws_s3_bucket.media_bucket.id
  policy = data.aws_iam_policy_document.s3_policy.json
}
