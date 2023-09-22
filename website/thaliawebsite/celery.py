import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "thaliawebsite.settings")

celery_app = Celery("thaliawebsite")

celery_app.config_from_object("django.conf:settings", namespace="CELERY")
