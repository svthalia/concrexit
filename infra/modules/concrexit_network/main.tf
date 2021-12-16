data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_vpc" "concrexit-vpc" {
  cidr_block = "10.0.0.0/16"

  assign_generated_ipv6_cidr_block = true

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
  })
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.concrexit-vpc.id

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
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
    Name = "${var.customer}-${var.stage}-concrexit"
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

  availability_zone = "${data.aws_region.current.name}a"

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
  })
}

resource "aws_network_interface" "concrexit-interface" {
  subnet_id       = aws_subnet.concrexit-subnet.id
  security_groups = [aws_security_group.concrexit-firewall.id]

  ipv6_address_count = 1

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-concrexit"
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
    Name = "${var.customer}-${var.stage}-concrexit"
  })
}

resource "aws_eip" "eip" {
  vpc               = true
  network_interface = aws_network_interface.concrexit-interface.id
  depends_on        = [aws_internet_gateway.gw]
}

output "aws_interface_id" {
  value = aws_network_interface.concrexit-interface.id
}

output "public_ipv4" {
  value = aws_eip.eip.public_ip
}

output "public_ipv6" {
  value = one(aws_network_interface.concrexit-interface.ipv6_addresses)
}
