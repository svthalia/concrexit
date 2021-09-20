data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_ebs_volume" "concrexit-postgres" {
  availability_zone = "${data.aws_region.current.name}a"
  size              = 20

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-postgres"
  })
}

resource "aws_ebs_volume" "concrexit-media" {
  availability_zone = "${data.aws_region.current.name}a"
  size              = 100

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-media"
  })
}

data "aws_ami" "nixos" {
  owners      = ["080433136561"] # NixOS
  most_recent = true

  filter {
    name   = "name"
    values = ["NixOS-21.05.*-x86_64-linux"]
  }
}

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

data "aws_route53_zone" "primary" {
  name = "thalia.nu"
}

resource "aws_eip" "eip" {
  instance = aws_instance.concrexit.id
  vpc      = true
}

resource "aws_route53_record" "www" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "staging-tf"
  type    = "A"
  ttl     = "300"
  records = [aws_eip.eip.public_ip]
}

resource "aws_instance" "concrexit" {
  ami           = data.aws_ami.nixos.id
  instance_type = "t3a.small"

  key_name = aws_key_pair.deployer.key_name

  root_block_device {
    volume_size = 50 # GiB
  }

  network_interface {
    network_interface_id = aws_network_interface.concrexit-interface.id
    device_index         = 0
  }

  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-nixos-concrexit"
  })
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

resource "aws_key_pair" "deployer" {
  key_name   = "${var.customer}-${var.stage}-concrexit-deployer-key"
  public_key = chomp(tls_private_key.ssh.public_key_openssh)
}

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = "4096"
}

module "deploy_nixos" {
  source = "../deploy_nixos"

  nixos_config = "${path.module}/../../nixos/configuration.nix"
  hermetic = true
  arguments = {
    "deploy_public_key" = chomp(tls_private_key.ssh.public_key_openssh)
  }

  target_user = "root"
  target_host = aws_eip.eip.public_ip

  // Will not be logged so can be marked as nonsensitive
  // Adviced by: https://github.com/hashicorp/terraform/issues/27154#issuecomment-814339127
  ssh_private_key = nonsensitive(tls_private_key.ssh.private_key_pem)

  triggers = {
    // Also re-deploy whenever the VM is re-created
    instance_id = aws_instance.concrexit.id
  }
}
