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
  acl    = "private"
  versioning {
    enabled = false
  }
  tags = merge(var.tags, {
    Name = "${var.customer}-${var.stage}-media"
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

  key_name             = aws_key_pair.deployer.key_name
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

resource "aws_key_pair" "deployer" {
  key_name   = "${var.customer}-${var.stage}-concrexit-deployer-key"
  public_key = var.ssh_public_key
}

locals {
  postgres_volname = replace(aws_volume_attachment.postgres-att.volume_id, "-", "")
  media_volname    = replace(aws_volume_attachment.media-att.volume_id, "-", "")
}

data "external" "nix-flake-build" {
  program = [
    "bash", "${abspath(path.module)}/nix-build-flake.sh"
  ]

  query = {
    flake_content = <<EOF
{
  description = "Concrexit deployment flake";

  inputs.concrexit.url = "${abspath("${path.module}/../../..")}";
  inputs.nixpkgs.follows = "concrexit/nixpkgs";

  outputs = { self, nixpkgs, concrexit }: {

    defaultPackage.x86_64-linux = (nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules =
        [
          "$${concrexit}/infra/nixos/concrexit.nix"
          "$${concrexit}/infra/nixos/swapfile.nix"
          ({ config, ... }: {
            nixpkgs.overlays = [ concrexit.overlay ];

            networking = {
              hostName = "${var.webhostname}";
              domain = "thalia.nu";
            };

            concrexit = {
              dir = "/volume/concrexit_media/data";
              domain = "${var.stage == "production" ? "thalia.nu" : "${var.webhostname}.thalia.nu"}";
              env-vars.GSUITE_DOMAIN = "${var.stage == "production" ? "thalia.nu" : "${var.webhostname}.thalia.nu"}";
              env-vars.GSUITE_MEMBERS_DOMAIN = "members.${var.stage == "production" ? "thalia.nu" : "${var.webhostname}.thalia.nu"}";
              env-vars.DJANGO_ENV = "${var.stage}";
              env-vars.AWS_STORAGE_BUCKET_NAME = "${aws_s3_bucket.concrexit-media-bucket.id}";
            };

            services.postgresql.dataDir = "/volume/concrexit_postgres/$${config.services.postgresql.package.psqlSchema}";

            systemd.tmpfiles.rules = [
              "d /volume/concrexit_postgres/$${config.services.postgresql.package.psqlSchema} 0750 postgres postgres - -"
            ];

            users.users.root.openssh.authorizedKeys.keys = [ "${var.ssh_public_key}" ];

            swapfile = {
              enable = true;
              size = "2GiB";
            };

            fileSystems."/volume/concrexit_postgres" = {
              autoFormat = true;
              fsType = "ext4";
              device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_${local.postgres_volname}";
            };

            fileSystems."/volume/concrexit_media" = {
              autoFormat = true;
              fsType = "ext4";
              device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_${local.media_volname}";
            };
          })
        ];
    }).config.system.build.toplevel;
  };
}
EOF
  }
}

resource "null_resource" "deploy_nixos" {
  triggers = {
    nix_build_output = data.external.nix-flake-build.result.out
  }

  connection {
    type        = "ssh"
    host        = var.public_ipv4
    user        = "root"
    timeout     = "100s"
    agent       = false
    private_key = chomp(var.ssh_private_key)
  }

  // Wait for the connection to succeed
  provisioner "remote-exec" {
    inline = [
      "true"
    ]
  }

  provisioner "local-exec" {
    command = <<EOF
workDir=$(mktemp -d)
trap 'rm -rf "$workDir"' EXIT
cd $workDir
echo "${chomp(var.ssh_private_key)}" > ./deploykey
chmod 600 ./deploykey
export NIX_SSHOPTS="-i ./deploykey -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o GlobalKnownHostsFile=/dev/null -o BatchMode=yes"
nix copy -s --to ssh://root@${var.public_ipv4} ${data.external.nix-flake-build.result.out}
EOF
  }

  provisioner "remote-exec" {
    inline = [
      "nix-env --profile /nix/var/nix/profiles/system --set ${data.external.nix-flake-build.result.out}",
      "${data.external.nix-flake-build.result.out}/bin/switch-to-configuration switch"
    ]
  }
}

output "public_ipv6" {
  value = aws_instance.concrexit.ipv6_addresses[0]
}
