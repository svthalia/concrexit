#! /bin/sh

chown -R appuser /volumes/static
chown -R appuser /volumes/media

# Wait for the main container to finish migrating.
until MANAGE_PY=1 runuser -u appuser -- ./manage.py migrate --check --no-input
do
    echo "Waiting for migrations to finish..."
    sleep 2
done

exec runuser -u appuser -- celery --app thaliawebsite worker \
    --loglevel INFO \
    --concurrency 4
