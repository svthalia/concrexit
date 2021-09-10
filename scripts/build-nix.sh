#!/usr/bin/env bash

# Convenience script to allow you to build concrexit via nix without
# needing to remember adding the args

if [ -z "$1" ] ; then
    attribute="machine"
else
	attribute=$1
fi

if [[ $# -gt 1 ]] ; then
    echo 'Usage: ./scripts/build-nix.sh [attribute to build (machine/vm/...)]'
    exit 1
fi


nix-build --argstr system "x86_64-linux" --argstr version "$(git rev-parse HEAD)" -A $attribute release.nix --show-trace
