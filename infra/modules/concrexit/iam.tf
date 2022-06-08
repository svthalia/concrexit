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
  name  = "${var.customer}-${var.stage}-concrexit-ec2-profile"
  roles = ["web_iam_role"]
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
