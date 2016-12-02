#!/bin/bash

set -e

until psql -h "$DJANGO_POSTGRES_HOST" -U "postgres" -c '\l'; do
    >&2 echo "PostgreSQL is unavailable: Sleeping"
    sleep 5
done
>&2 echo "PostgreSQL is up"

chown -R 33:33 /concrexit/

cd /usr/src/app
>&2 echo "Running site with uwsgi"
uwsgi --chdir /usr/src/app \
    --socket :8000 \
    --socket-timeout 1800 \
    --uid 33 \
    --gid 33 \
    --threads 5 \
    --processes 5 \
    --module thaliawebsite.wsgi:application \
    --harakiri 1800 \
    --master \
    --max-requests 5000 \
    --vacuum \
    --limit-post 0 \
    --post-buffering 16384 \
    --logto '/concrexit/log/uwsgi.log'
