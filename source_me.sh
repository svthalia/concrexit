#!/bin/bash
pathname=$_

if [[ "$pathname" = "$0" ]]; then
    echo "Remember: you need to run me as 'source ./source_me.sh', not execute it!"
    return
fi

if [ -d venv ]; then
    source venv/bin/activate
else
    pyvenv venv
    source venv/bin/activate
fi
