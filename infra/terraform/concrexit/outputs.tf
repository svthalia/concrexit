output "cloudfront_public_key_id" {
  description = "ID of the CloudFront public key to be passed as environment variable to the server"
  value       = module.cdn.cloudfront_public_key_id
}
