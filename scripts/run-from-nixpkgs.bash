#!/usr/bin/env bash

# Runs a program from our pinned nixpkgs
# Usage:
# scripts/run-from-nixpkgs git

set -x

nix-shell $(nix eval --raw '(import nix/sources.nix).nixpkgs') -p $1 --run "$*"
