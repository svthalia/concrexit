#! /bin/sh

chown -R appuser /volumes/static
chown -R appuser /volumes/media

MANAGE_PY=1 runuser -u appuser -- ./manage.py collectstatic --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py migrate --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py createcachetable


exec runuser -u appuser -- /venv/bin/gunicorn \
  --config=/app/gunicorn.conf.py \
  thaliawebsite.wsgi:application
