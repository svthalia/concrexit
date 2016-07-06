#!/bin/bash

echo "run me as 'source ./source_me.sh', not as './source_me.sh'!"

if [ -d venv ]; then
    source venv/bin/activate
else
    pyvenv venv
    source venv/bin/activate
fi
