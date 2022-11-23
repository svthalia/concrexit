#! /bin/sh

chown -R appuser /media
MANAGE_PY=1 /venv/bin/python manage.py migrate --no-input
exec runuser -u appuser -- /venv/bin/gunicorn --bind 0.0.0.0:8000 --log-level info --workers 4 --capture-output thaliawebsite.wsgi:application
