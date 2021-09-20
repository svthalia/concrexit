{
  description = "Concrexit";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/release-21.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

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

        devShells = (flake-utils.lib.flattenTree
          {
            concrexit = pkgs.concrexit;
          });
        
        devShell = pkgs.mkShell { packages = with pkgs; [ poetry ]; };

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
          # We define two variants of the NixOS system, the vm can be used to do local testing.
          # A script to run this VM is included in the scripts directory. Unfortunately this
          # will only work on a Linux system.
          vm = (
            import (nixpkgs + "/nixos") {
              configuration = {
                imports = [ ./infra/nixos/concrexit.nix (nixpkgs + "/nixos/modules/profiles/qemu-guest.nix") ];

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

                concrexit.local-testing = true;

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
