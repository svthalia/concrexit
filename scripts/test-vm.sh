#! /usr/bin/env -S nix shell nixpkgs#bash nixpkgs#shellcheck nixpkgs#nix nixpkgs#git nixpkgs#jq nixpkgs#coreutils --ignore-environment --command bash
# shellcheck shell=bash
set -xveuo pipefail
shellcheck "$0" || exit 1

machine=$(nix build --no-link --json '.#vm' | jq --raw-output '.[0].outputs.out')

# Remove the VM disk after this script finishes
trap 'rm --force staging.qcow2' EXIT

QEMU_NET_OPTS='hostfwd=tcp::8001-:80' "$machine/bin/run-staging-vm" -nographic
