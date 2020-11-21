#!/usr/bin/env bash

# Used for building the configuration locally, ideally this script shouldn't
# be used. Instead you should add changes to git and let it autodeploy using
# GitHub Actions.

set -e

# The arg is needed to allow a macOS system to evaluate the config,
# building the machine will require a Linux build system though.
machine=$(nix-build --arg system \"x86_64-linux\" -A machine release.nix --show-trace)
nix-copy-closure --to $USER@staging.thalia.nu $machine
ssh $USER@staging.thalia.nu -- sudo $machine/bin/switch-to-configuration switch
