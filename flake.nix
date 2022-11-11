{
  description = "Concrexit server";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
  inputs.agenix.url = "github:ryantm/agenix";

  outputs = { self, nixpkgs, agenix } @attrs:
    {
      nixosConfigurations."production" = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs = attrs;
        modules =
          [
            ./timed-commands.nix
            ./concrexit-server.nix
            agenix.nixosModule
            ({ pkgs, modulesPath, ... }: {
              imports = [ "${modulesPath}/virtualisation/amazon-image.nix" ];

              networking.hostName = "production";

              fileSystems."/var/lib/concrexit/media" = {
                options = [ "bind" ];
                device = "/volume/concrexit_media/data/media";
              };

              # These IDs should roll out of the terraform deploy
              fileSystems."/volume/concrexit_postgres" = {
                autoFormat = true;
                fsType = "ext4";
                device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol0e5e69d37ef0403cd";
              };
              fileSystems."/volume/concrexit_media" = {
                autoFormat = true;
                fsType = "ext4";
                device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol038f8a5488e8c45a9";
              };
            })
          ];
      };

      nixosConfigurations."staging" = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs = attrs;
        modules =
          [
            ./timed-commands.nix
            ./concrexit-server.nix
            agenix.nixosModule
            ({ pkgs, modulesPath, ... }: {
              imports = [ "${modulesPath}/virtualisation/amazon-image.nix" ];

              networking.hostName = "staging";

              fileSystems."/var/lib/concrexit/media" = {
                options = [ "bind" ];
                device = "/volume/concrexit_media/data/media";
              };

              fileSystems."/volume/concrexit_postgres" = {
                autoFormat = true;
                fsType = "ext4";
                device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol08fe0bca8fe7d9784";
              };
              fileSystems."/volume/concrexit_media" = {
                autoFormat = true;
                fsType = "ext4";
                device = "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol02368558eb1fb099a";
              };
            })
          ];
      };
    };
}
