#! /usr/bin/env bash

set -euo pipefail

workDir=/Users/jelle/dev/thalia/concrexit_flake
cd $workDir

jq -r '.flake_content' > flake.nix

nix flake update
nix build --log-format raw --verbose '.#defaultPackage.x86_64-linux' --json | jq -r .[0].outputs
