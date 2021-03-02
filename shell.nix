# This file is for the nix-shell command. It installs the pre-commit-check
# and loads the programs from the devTools list

{ project ? import ./nix { version = "git"; system = builtins.currentSystem; }
}:

project.pkgs.mkShell {
  buildInputs = project.devTools;
  shellHook = ''
    ${project.pre-commit-check.shellHook}
  '';
}
