data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_ebs_volume" "concrexit-postgres" {
  availability_zone = "eu-west-1a"
  size              = 20

  tags = merge(var.tags, {
    Name     = "${var.customer}-${var.stage}-postgres",
    Snapshot = true
  })
}

resource "aws_ebs_volume" "concrexit-media" {
  availability_zone = "eu-west-1a"
  size              = 100

  tags = merge(var.tags, {
    Name     = "${var.customer}-${var.stage}-media",
    Snapshot = true
  })
}

resource "aws_s3_bucket" "concrexit-media-bucket" {
  bucket = "${var.customer}-${var.stage}-media"
  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-media"
  })
}

resource "aws_s3_bucket_acl" "example_bucket_acl" {
  bucket = aws_s3_bucket.concrexit-media-bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "versioning_example" {
  bucket = aws_s3_bucket.concrexit-media-bucket.id
  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_volume_attachment" "postgres-att" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.concrexit-postgres.id
  instance_id = aws_instance.concrexit.id
}

resource "aws_volume_attachment" "media-att" {
  device_name = "/dev/sdg"
  volume_id   = aws_ebs_volume.concrexit-media.id
  instance_id = aws_instance.concrexit.id
}

data "aws_ami" "nixos" {
  owners      = ["080433136561"] # NixOS
  most_recent = true

  filter {
    name   = "name"
    values = ["NixOS-21.11.*-x86_64-linux"]
  }
}

resource "aws_instance" "concrexit" {
  ami           = data.aws_ami.nixos.id
  instance_type = "t3a.small"

  iam_instance_profile = aws_iam_instance_profile.concrexit-ec2-profile.id

  root_block_device {
    volume_size = 50 # GiB
  }

  network_interface {
    network_interface_id = var.aws_interface_id
    device_index         = 0
  }

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-nixos-concrexit"
  })
}

locals {
  postgres_volname = replace(aws_volume_attachment.postgres-att.volume_id, "-", "")
  media_volname    = replace(aws_volume_attachment.media-att.volume_id, "-", "")
}
