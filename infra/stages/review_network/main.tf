terraform {
  required_version = ">=0.14.10"

  required_providers {
    aws = ">= 3.28.0"
  }

  backend "s3" {
    bucket  = "thalia-terraform-state"
    key     = "concrexit/reviewnetwork.tfstate"
    region  = "eu-west-1"
    profile = "thalia"
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

resource "aws_vpc" "concrexit-vpc" {
  cidr_block = "10.0.0.0/16"

  assign_generated_ipv6_cidr_block = true

  tags = merge(var.tags, {
    Name = "${var.customer}-review-concrexit"
  })
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.concrexit-vpc.id

  tags = merge(var.tags, {
    Name = "${var.customer}-review-concrexit"
  })
}

resource "aws_route_table" "routes" {
  vpc_id = aws_vpc.concrexit-vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  route {
    ipv6_cidr_block = "::/0"
    gateway_id      = aws_internet_gateway.gw.id
  }

  tags = merge(var.tags, {
    Name = "${var.customer}-review-concrexit"
  })
}

resource "aws_route_table_association" "route_assoc" {
  subnet_id      = aws_subnet.concrexit-subnet.id
  route_table_id = aws_route_table.routes.id
}

resource "aws_subnet" "concrexit-subnet" {
  vpc_id = aws_vpc.concrexit-vpc.id

  cidr_block                      = "10.0.0.0/24"
  ipv6_cidr_block                 = replace(aws_vpc.concrexit-vpc.ipv6_cidr_block, "::/56", "::/64")
  map_public_ip_on_launch         = true
  assign_ipv6_address_on_creation = true

  depends_on = [aws_internet_gateway.gw]

  availability_zone = "${var.aws_region}a"

  tags = merge(var.tags, {
    Name = "${var.customer}-review-concrexit"
  })
}

resource "aws_security_group" "concrexit-firewall" {
  description = "Allow HTTP and SSH inbound traffic"
  vpc_id      = aws_vpc.concrexit-vpc.id

  ingress {
    description      = "SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.customer}-review-concrexit"
  })
}

