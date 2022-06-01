{
  description = "Concrexit";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";
  inputs.poetry2nix.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      version = self.shortRev or null;
    in
    (flake-utils.lib.eachSystem supportedSystems (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            self.overlay
            poetry2nix.overlay
          ];
        };
      in
      rec {

        devShells =
          let basePackages = with pkgs; [ poetry pkgs.concrexit ghostscript file ];
          in
          (flake-utils.lib.flattenTree
            {
              concrexit = pkgs.mkShell {
                packages = basePackages;
              };
              deployment = pkgs.mkShell {
                packages = with pkgs; [ terraform jq ];
              };
            });

        devShell = devShells.concrexit;

        packages = (flake-utils.lib.flattenTree
          {
            concrexit = pkgs.concrexit;
          } // (nixpkgs.lib.optionalAttrs (builtins.elem system [ "x86_64-linux" "aarch64-linux" ]) {
          # Generate an .img file that can be uploaded to AWS to create an AMI.
          amazonImage = (
            import (nixpkgs + "/nixos") {
              configuration = {
                imports = [ ./infra/nixos/concrexit.nix (nixpkgs + "/nixos/maintainers/scripts/ec2/amazon-image.nix") ];

                nixpkgs.pkgs = pkgs;

                amazonImage.sizeMB = 4096;
              };

              inherit system;
            }
          ).config.system.build.amazonImage;

          # This vm can be used to do local testing.
          # A script to run this VM is included in the scripts directory. Unfortunately this
          # will only work on a Linux system.
          vm = (
            import (nixpkgs + "/nixos") {
              configuration = {
                imports = [ ./infra/nixos/concrexit.nix (nixpkgs + "/nixos/modules/virtualisation/qemu-vm.nix") ];

                nixpkgs.pkgs = pkgs;

                networking.hostName = "staging";
                networking.hosts = pkgs.lib.mkForce { };

                services.getty.helpLine = ''
                  You can log in to the root user with an empty password. To exit this console, type Ctrl+A then x.
                '';

                users.motd = ''
                  You are on a testing VM for concrexit. You will probably want to run some setup:
                  concrexit-manage createfixtures -a
                  concrexit-manage createsuperuser
                  (but first check if concrexit has started up with journalctl -fu concrexit)
                '';

                users = {
                  users.root.password = "";
                };

                virtualisation = {
                  cores = 2;
                  memorySize = 4096;
                };
              };

              inherit system;
            }
          ).vm;
        }));

        defaultPackage = packages.concrexit;

      })) // {
      overlay = final: prev: {
        concrexit = final.callPackage ./default.nix { inherit version; };
      };
    };
}
