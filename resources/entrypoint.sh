#!/bin/bash

set -e

if [[ ! -z "$DJANGO_POSTGRES_HOST" ]]; then
  until psql -h "$DJANGO_POSTGRES_HOST" -U "postgres" -c '\l'; do
      >&2 echo "PostgreSQL is unavailable: Sleeping"
      sleep 5
  done
  >&2 echo "PostgreSQL is up"
fi


cd /usr/src/app/website/
>&2 echo "Running ./manage.py $@"
exec ./manage.py $@
