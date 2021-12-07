#! /usr/bin/env bash

nix flake update
nix build '.#defaultPackage.x86_64-linux' --json | jq -r .[0].outputs
