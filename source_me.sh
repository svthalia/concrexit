#!/bin/bash
pathname=$_

if [[ "$pathname" != "$0" ]]; then
    echo "Rember: you need to run me as 'source ./source_me.sh', execute it!"
    echo "So if shit doesn't work, try that (you may have alrd"
    return
fi

if [ -d venv ]; then
    source venv/bin/activate
else
    pyvenv venv
    source venv/bin/activate
fi
