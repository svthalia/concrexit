{ sources ? import ./sources.nix, system ? builtins.currentSystem }:
let
  # Helper program that creates a derivation which contains the source without
  # the files ignored by git
  gitignoreSource = (import sources."gitignore.nix" { inherit (pkgs) lib; }).gitignoreSource;
  src = gitignoreSource ./..;

  overlay = self: _super: {
    poetry2nix = self.callPackage sources."poetry2nix" { };
    # This allows us to use pkgs.concrexit everywhere we need the concrexit package
    concrexit = self.callPackage ./concrexit.nix { inherit src; };
  };

  # Import nixpkgs from the sources managed by niv, this makes sure
  # nixpkgs changes only when we want to
  pkgs = import sources.nixpkgs { localSystem.system = system; overlays = [ overlay ]; };

  # Helper program that does certain sanity checks on the nix/shell source
  pre-commit-hooks = (import sources."pre-commit-hooks.nix");

  pre-commit-check = pre-commit-hooks.run {
    inherit src;
    hooks = {
      shellcheck.enable = true;
      nixpkgs-fmt.enable = true;
      nix-linter.enable = true;
    };
    # generated files
    excludes = [ "^nix/sources\.nix$" ];
  };

in
{
  inherit pkgs src pre-commit-check;

  devTools = [
    pre-commit-hooks.pre-commit
    pre-commit-hooks.nixpkgs-fmt
    pkgs.concrexit.env
    pkgs.niv
  ];
}
