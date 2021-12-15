#!/usr/bin/env bash

set -euo pipefail

if [[ ! -f "flake.nix" ]]; then
    echo "Run this script from the repository root directory"
    exit 1
fi

if [[ -z ${IN_NIX_SHELL+x} ]]; then
    exec env IN_NIX_SHELL=1 nix shell nixpkgs#bash nixpkgs#nix nixpkgs#git nixpkgs#jq nixpkgs#coreutils --inputs-from '.' --command bash $0 "$@"
    exit 0
fi

set -x

