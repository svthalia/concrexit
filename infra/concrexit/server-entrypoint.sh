#! /bin/sh

chown -R appuser /volumes/static
chown -R appuser /volumes/media

MANAGE_PY=1 runuser -u appuser -- ./manage.py collectstatic --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py migrate --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py createcachetable


exec runuser -u appuser -- /venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --log-level info \
    --worker-class gthread \
    --workers 4 \
    --threads 4 \
    --timeout 240 \
    --capture-output thaliawebsite.wsgi:application \
