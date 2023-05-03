data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# EC2 instance =========================================================================

resource "aws_key_pair" "concrexit_ssh_key" {
  key_name   = "${var.customer}-${var.stage}-concrexit-ssh-key"
  public_key = var.ssh_public_key

  tags = var.tags
}

resource "aws_instance" "concrexit" {
  ami           = var.ec2_ami
  instance_type = var.ec2_instance_type

  iam_instance_profile = aws_iam_instance_profile.concrexit-ec2-profile.id

  root_block_device {
    volume_size = 30
  }

  network_interface {
    network_interface_id = var.aws_interface_id
    device_index         = 0
  }

  key_name = aws_key_pair.concrexit_ssh_key.key_name

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
  })
}

# EBS volume for postgres ==============================================================

resource "aws_ebs_volume" "concrexit-postgres" {
  availability_zone = "eu-west-1a"
  size              = 10

  tags = merge(var.tags, {
    Name     = "${var.customer}-${var.stage}-postgres",
    Snapshot = true
  })
}

resource "aws_volume_attachment" "postgres-att" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.concrexit-postgres.id
  instance_id = aws_instance.concrexit.id
}

# S3 bucket for media ==================================================================

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
    status = "Suspended"
  }
}

# IAM role for EC2 to access the S3 bucket =============================================

resource "aws_iam_role" "concrexit-iam-role" {
  name               = "${var.customer}-${var.stage}-concrexit-iam-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "concrexit-ec2-profile" {
  name = "${var.customer}-${var.stage}-concrexit-ec2-profile"
  role = aws_iam_role.concrexit-iam-role.id
}

resource "aws_iam_role_policy" "concrexit-iam-role-policy" {
  name   = "${var.customer}-${var.stage}-concrexit-iam-role-policy"
  role   = aws_iam_role.concrexit-iam-role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["${aws_s3_bucket.concrexit-media-bucket.arn}"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": ["${aws_s3_bucket.concrexit-media-bucket.arn}/*"]
    }
  ]
}
EOF
}
