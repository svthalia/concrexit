#! /bin/sh

MANAGE_PY=1 /venv/bin/python manage.py migrate
exec /venv/bin/gunicorn --bind 0.0.0.0:8000 --log-level debug -w 4 thaliawebsite.wsgi:application
