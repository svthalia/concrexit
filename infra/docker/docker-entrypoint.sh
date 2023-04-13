#! /bin/sh

chown -R appuser /media
MANAGE_PY=1 runuser -u appuser -- /venv/bin/python manage.py migrate --no-input
exec runuser -u appuser -- /venv/bin/gunicorn --bind 0.0.0.0:8000 --log-level info --workers 4 --threads 20 --timeout 240 --capture-output thaliawebsite.wsgi:application