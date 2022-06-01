{
  description = "Concrexit deployment flake";

  inputs.concrexit.url = "/Users/jelle/dev/thalia/concrexit";
  inputs.nixpkgs.follows = "concrexit/nixpkgs";

  outputs = { self, nixpkgs, concrexit }: {

    nixosConfigurations."production" = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules =
        [
          "${concrexit}/infra/nixos/concrexit.nix"
          "${concrexit}/infra/nixos/swapfile.nix"
          ({ config, ... }: {
            nixpkgs.overlays = [ concrexit.overlay ];

            networking = {
              hostName = "production";
              domain = "thalia.nu";
            };

            concrexit = {
              dir = "/volume/concrexit_media/data";
              domain = "thalia.nu";
              env-vars.GSUITE_DOMAIN = "thalia.nu";
              env-vars.GSUITE_MEMBERS_DOMAIN = "members.thalia.nu";
              env-vars.DJANGO_ENV = "production";
            };

            services.postgresql.dataDir = "/volume/concrexit_postgres/${config.services.postgresql.package.psqlSchema}";

            systemd.tmpfiles.rules = [
              "d /volume/concrexit_postgres/${config.services.postgresql.package.psqlSchema} 0750 postgres postgres - -"
            ];

            users.users.root.openssh.authorizedKeys.keys = [ "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICunYiTe1MOJsGC5OBn69bewMBS5bCCE1WayvM4DZLwE jelle@Jelles-MacBook-Pro.local" ];

            fileSystems."/volume/concrexit_postgres" = {
              autoFormat = true;
              fsType = "ext4";
              device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol0e5e69d37ef0403cd-ns-1";
            };

            fileSystems."/volume/concrexit_media" = {
              autoFormat = true;
              fsType = "ext4";
              device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol038f8a5488e8c45a9-ns-1";
            };
          })
        ];
    };
  };
}
