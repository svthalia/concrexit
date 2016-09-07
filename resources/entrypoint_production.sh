#!/bin/bash

set -e

until psql -h "$DJANGO_POSTGRES_HOST" -U "postgres" -c '\l'; do
    >&2 echo "PostgreSQL is unavailable: Sleeping"
    sleep 5
done
>&2 echo "PostgreSQL is up"

cd /usr/src/app
>&2 echo "Running site with uwsgi"
uwsgi --chdir /usr/src/app \
    --socket :8000 \
    --threads 2 \
    --processes 4 \
    --module thaliawebsite.wsgi:application \
    --lazy-app \
    --harakiri 20 \
    --max-requests 5000 \
    --vacuum \
    --logto '/log/uwsgi.log'
