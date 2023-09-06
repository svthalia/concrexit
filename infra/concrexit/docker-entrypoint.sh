#! /bin/sh

chown -R appuser /volumes/static
chown -R appuser /volumes/media

MANAGE_PY=1 runuser -u appuser -- ./manage.py collectstatic --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py migrate --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py createcachetable

# Store all environment variables in /etc/environment for cron to use.
printenv > /etc/environment

# Start cron daemon.
cron

exec runuser -u appuser -- /venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --log-level info \
    --workers 4 \
    --threads 20 \
    --timeout 240 \
    --capture-output thaliawebsite.wsgi:application \
