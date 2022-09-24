output "public_ipv6" {
  value = aws_instance.concrexit.ipv6_addresses[0]
}

output "postgres_volname" {
  value = local.postgres_volname
}

output "media_volname" {
  value = local.media_volname
}

output "media_bucket_id" {
  value = aws_s3_bucket.concrexit-media-bucket.id
}
