data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_ebs_volume" "concrexit-postgres" {
  availability_zone = data.aws_network_interface.concrexit-interface.availability_zone
  size              = 20

  tags = merge(var.tags, {
    Name     = "${var.customer}-${var.stage}-postgres",
    Snapshot = true
  })
}

resource "aws_ebs_volume" "concrexit-media" {
  availability_zone = data.aws_network_interface.concrexit-interface.availability_zone
  size              = 100

  tags = merge(var.tags, {
    Name     = "${var.customer}-${var.stage}-media",
    Snapshot = true
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

data "aws_network_interface" "concrexit-interface" {
  id = var.aws_interface_id
}

resource "aws_instance" "concrexit" {
  ami           = data.aws_ami.nixos.id
  instance_type = "t3a.small"
  availability_zone = data.aws_network_interface.concrexit-interface.availability_zone

  key_name = aws_key_pair.deployer.key_name

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
  public_ipv4      = coalesce(var.public_ipv4, aws_instance.concrexit.public_ip)
}

data "external" "nix-flake-build" {
  program = [
    "bash", "${abspath(path.module)}/nix-build-flake.sh"
  ]

  working_dir = path.module

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
              hostName = "${var.hostname}";
              domain = "${var.hostdomain}";
            };

            concrexit = {
              dir = "/volume/concrexit_media/data";
              domain = "${var.webdomain}";
              env-vars.GSUITE_DOMAIN = ${jsonencode(var.gsuite_domain)};
              env-vars.GSUITE_MEMBERS_DOMAIN = ${jsonencode(var.gsuite_members_domain)};
              env-vars.DJANGO_ENV = "${var.django_env}";
              ssl = true;
            };

            services.postgresql.dataDir = "/volume/concrexit_postgres/$${config.services.postgresql.package.psqlSchema}";

            systemd.services.postgres-dir = {
              wantedBy = [ "multi-user.target" ];
              after = [ "volume-concrexit_postgres.mount" ];
              script = ''
                mkdir --parents "/volume/concrexit_postgres/$${config.services.postgresql.package.psqlSchema}"
                chown postgres:postgres "/volume/concrexit_postgres/$${config.services.postgresql.package.psqlSchema}"
              '';
            };
            systemd.services.postgresql.after = [ "postgres-dir.service" ];
            systemd.services.concrexit-dir.after = [ "volume-concrexit_media.mount" ];

            users.users.root.openssh.authorizedKeys.keys = [ "${var.ssh_public_key}" ];

            swapfile = {
              enable = true;
              size = "2GiB";
            };

            fileSystems."/volume/concrexit_postgres" = {
              autoFormat = true;
              fsType = "ext4";
              device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_${local.postgres_volname}-ns-1";
            };

            fileSystems."/volume/concrexit_media" = {
              autoFormat = true;
              fsType = "ext4";
              device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_${local.media_volname}-ns-1";
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
    host        = local.public_ipv4
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
nix copy -s --to ssh://root@${local.public_ipv4} ${data.external.nix-flake-build.result.out}
EOF
  }

  provisioner "remote-exec" {
    inline = [
      "nix-env --profile /nix/var/nix/profiles/system --set ${data.external.nix-flake-build.result.out}",
      "${data.external.nix-flake-build.result.out}/bin/switch-to-configuration switch"
    ]
  }
}

output "public_ipv4" {
  value = local.public_ipv4
}

output "public_ipv6" {
  value = aws_instance.concrexit.ipv6_addresses[0]
}
