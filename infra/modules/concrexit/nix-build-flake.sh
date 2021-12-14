#! /usr/bin/env bash

set -e

workDir=$(mktemp -d)
trap 'rm -rf "$workDir"' EXIT
cd $workDir

jq -r '.flake_content' > flake.nix

nix flake update
nix build '.#defaultPackage.x86_64-linux' --json | jq -r .[0].outputs
