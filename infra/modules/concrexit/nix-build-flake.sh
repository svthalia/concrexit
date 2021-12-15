#! /usr/bin/env bash

set -euo pipefail

workDir=$(mktemp -d)
trap 'rm -rf "$workDir"' EXIT
cd $workDir

jq -r '.flake_content' > flake.nix

nix flake update
nix build --log-format raw --verbose '.#defaultPackage.x86_64-linux' --json | jq -r .[0].outputs
