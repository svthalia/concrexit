#!/bin/sh
if [ ! -f "./index.rst" ]; then
    >&2 echo "Run me from the docs/ folder!"
    exit 1
fi

sphinx-apidoc -M -f -o . ../website ../website/*/migrations ../website/*/tests* ../website/manage.py
