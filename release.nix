# The releas.nix file builds everything that is needed to release a version
# of concrexit. This is not only the concrexit package, but also the NixOS
# system that runs the web service and database.

{ sources ? import ./nix/sources.nix, version, system ? builtins.currentSystem }:
let
  inherit (import ./nix { inherit sources version system; }) pre-commit-check src pkgs;

  # We define two variants of the NixOS system, the vm can be used to do local testing.
  # A script to run this VM is included in the scripts directory. Unfortunately this
  # will only work on a Linux system.
  vm = (
    import "${sources.nixpkgs}/nixos" {
      configuration = {
        imports = [ ./nix/configuration.nix "${sources.nixpkgs}/nixos/modules/profiles/qemu-guest.nix" ];

        nixpkgs.pkgs = pkgs;

        networking.hostName = "staging";
        networking.hosts = pkgs.lib.mkForce { };

        services.mingetty.helpLine = ''
          You can log in to the root user with an empty password. To exit this console, type Ctrl+A then x.
        '';

        users.motd = ''

          You are on a testing VM for concrexit. You will probably want to run some setup:
          concrexit-manage createfixtures -a
          concrexit-manage createsuperuser
          (but first check if concrexit has started up with journalctl -fu concrexit)
        '';

        concrexit.ssl = false;

        users = {
          users.root.password = "";
        };

        virtualisation = {
          cores = 2;

          memorySize = "4096";
        };
      };
      system = "x86_64-linux";
    }
  ).vm;

  machine = (
    import "${sources.nixpkgs}/nixos" {
      configuration = {
        imports = [ ./nix/configuration.nix "${sources.nixpkgs}/nixos/modules/virtualisation/amazon-image.nix" ];

        nixpkgs.pkgs = pkgs;

        networking.hostName = "staging";
        networking.domain = "thalia.nu";
        # This is needed because otherwise socket.getfqdn() breaks in Python
        networking.hosts = pkgs.lib.mkForce { };
        users.motd = ''
          You are on the concrexit staging server
        '';

        concrexit.ssl = true;
      };
      system = "x86_64-linux";
    }
  ).system;

  test = pkgs.nixosTest ./nix/test.nix;
in
{
  # Instead of a regular attrset we use this aggregate function which might help
  # if we want to use Hydra in the future
  concrexit-release = pkgs.releaseTools.aggregate {
    name = "concrexit";

    constituents = [
      pre-commit-check
      pkgs.concrexit
      vm
      machine
      test
    ];
  };

  github-actions = pkgs.releaseTools.aggregate {
    name = "ci";

    constituents = [
      pre-commit-check
      pkgs.concrexit
      vm
      machine
    ];
  };

  # This is to make sure we can do -A machine to only build the machine in nix-build
  inherit (pkgs) concrexit;
  inherit vm machine test;
}
