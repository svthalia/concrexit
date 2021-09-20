{ deploy_public_key }:
let
  system = "x86_64-linux";

  concrexit-flake = (import (fetchTarball https://github.com/edolstra/flake-compat/archive/master.tar.gz) {
    src = ../../.;
  }).defaultNix;

  nixpkgs = concrexit-flake.inputs.nixpkgs;
in
import "${nixpkgs}/nixos" {
  inherit system;
  configuration = {
    imports = [ ./concrexit.nix ./swapfile.nix ];
    nixpkgs.overlays = [ concrexit-flake.overlay ];

    swapfile = {
      enable = true;
      size = "2GiB";
    };

    # After the first deploy the generated root key should still be usable
    users.users.root.openssh.authorizedKeys.keys = [ deploy_public_key ];
  };
}
