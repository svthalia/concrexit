import logging
from importlib import import_module

from django.apps import apps
from django.conf import settings

from celery import shared_task
from oauth2_provider.models import clear_expired

from utils.snippets import minimise_logentries_data

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@shared_task
def data_minimisation():
    for app in apps.get_app_configs():
        try:
            app.execute_data_minimisation(dry_run=False)
        except Exception as e:
            logger.warning("Minimization failed: %s", e)

    count = minimise_logentries_data(dry_run=False)
    logger.info("Removed %d log entries", count)


@shared_task
def clean_up():
    engine = import_module(settings.SESSION_ENGINE)
    engine.SessionStore.clear_expired()


@shared_task
def clear_tokens():
    clear_expired()
