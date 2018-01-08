#!/bin/bash

set -e

sphinx-build -b html /usr/src/app/docs/ /concrexit/docs/

until psql -h "$DJANGO_POSTGRES_HOST" -U "postgres" -c '\l'; do
    >&2 echo "PostgreSQL is unavailable: Sleeping"
    sleep 5
done
>&2 echo "PostgreSQL is up"

cd /usr/src/app/website/
>&2 echo "Running ./manage.py $@"
./manage.py $@
