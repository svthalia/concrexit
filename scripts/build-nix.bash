#!/usr/bin/env bash

# Convenience script to allow you to build concrexit via nix without
# needing to remember adding the args

if [ -z "$1" ] ; then
    attribute="machine"
else
	attribute="$1"
fi

if [ -z "$2" ] ; then
	version="$2"
else
	version=$(git rev-parse HEAD)
fi

if [[ $# -gt 2 ]] ; then
    echo 'Usage: ./scripts/build-nix.sh [attribute to build (machine/vm/...)] [version]'
    exit 1
fi


exec nix-build --arg system \"x86_64-linux\" --arg version "\"$version\"" -A $attribute release.nix --show-trace
