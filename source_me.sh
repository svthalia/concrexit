#!/bin/bash

echo "Rember: you need to run me as 'source ./source_me.sh', not as './source_me.sh'!"
echo "So if shit doesn't work, try that (you may have alrd"

if [ -d venv ]; then
    source venv/bin/activate
else
    pyvenv venv
    source venv/bin/activate
fi
