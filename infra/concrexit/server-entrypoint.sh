#! /bin/sh

chown -R appuser /volumes/static
chown -R appuser /volumes/media

if [ ! -f /app/.collectstatic_done ]; then # Only run collectstatic if it hasn't been run before in this container.s
    MANAGE_PY=1 runuser -u appuser -- ./manage.py collectstatic --no-input && touch /app/.collectstatic_done
fi
MANAGE_PY=1 runuser -u appuser -- ./manage.py migrate --no-input
MANAGE_PY=1 runuser -u appuser -- ./manage.py createcachetable


exec runuser -u appuser -- /venv/bin/gunicorn \
  --config /app/gunicorn.conf.py \
  thaliawebsite.wsgi:application
