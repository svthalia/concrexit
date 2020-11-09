#!/bin/bash

set -e

chown -R www-data:www-data /concrexit/

until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${DJANGO_POSTGRES_HOST}" -U "${POSTGRES_USER}" -c '\l' "${POSTGRES_DB}"; do
    >&2 echo "PostgreSQL is unavailable: Sleeping"
    sleep 5
done
>&2 echo "PostgreSQL is up"

cd /usr/src/app/website/

./manage.py collectstatic --no-input
./manage.py migrate --no-input
./manage.py compress --force

>&2 echo "Running site with uwsgi"
exec uwsgi --chdir /usr/src/app/website \
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
    --thunder-lock \
    --logto '/concrexit/log/uwsgi.log' \
    --ignore-sigpipe \
    --ignore-write-errors \
    --disable-write-exception
