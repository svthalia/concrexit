#! /usr/bin/env bash

set -eo pipefail

if [[ -n "$CONCREXIT_NIX_DEBUG" ]]; then
    workDir="../../../../concrexit_flake"
    mkdir -p $workDir
else
    workDir=$(mktemp -d)
    trap 'rm -rf "$workDir"' EXIT
fi

cd $workDir

jq -r '.flake_content' > flake.nix

nix flake update
nix build --log-format raw --verbose '.#defaultPackage.x86_64-linux' --json | jq -r .[0].outputs
