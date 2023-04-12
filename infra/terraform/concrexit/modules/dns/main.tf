data "aws_route53_zone" "primary" {
  name = var.zone_name
}

resource "aws_route53_record" "www" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = var.webdomain
  type            = "A"
  ttl             = "300"
  records         = [var.public_ipv4]
  allow_overwrite = true
}

resource "aws_route53_record" "www-ipv6" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = var.webdomain
  type            = "AAAA"
  ttl             = "300"
  records         = [var.public_ipv6]
  allow_overwrite = true
}

resource "aws_route53_record" "wildcard" {
  zone_id         = data.aws_route53_zone.primary.zone_id
  name            = "*.${var.webdomain}"
  type            = "CNAME"
  ttl             = "300"
  records         = [var.webdomain]
  allow_overwrite = true
}
