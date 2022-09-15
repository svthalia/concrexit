#! /bin/sh

MANAGE_PY=1 /venv/bin/python manage.py collectstatic --no-input
MANAGE_PY=1 /venv/bin/python manage.py compress
