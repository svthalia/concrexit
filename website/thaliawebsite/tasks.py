import logging
from importlib import import_module

from django.conf import settings

from celery import shared_task
from oauth2_provider.models import clear_expired

from events import services as events_services
from facedetection import services as facedetection_services
from members import services as members_services
from payments import services as payments_services
from pizzas import services as pizzas_services
from sales import services as sales_services
from utils.snippets import minimise_logentries_data

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@shared_task
def data_minimisation():
    processed = members_services.execute_data_minimisation()
    for p in processed:
        logger.info(f"Removed data for {p}")

    processed = events_services.execute_data_minimisation()
    for p in processed:
        logger.info(f"Removed registration information for {p}")

    processed = payments_services.execute_data_minimisation()
    for p in processed:
        logger.info(f"Removed payments information for {p}")

    processed = pizzas_services.execute_data_minimisation()
    for p in processed:
        logger.info(f"Removed food events information for {p}")

    processed = sales_services.execute_data_minimisation()
    for p in processed:
        logger.info(f"Removed sales orders for {p}")

    processed = facedetection_services.execute_data_minimisation()
    for p in processed:
        logger.info(f"Removed reference faces: {p}")

    processed = minimise_logentries_data()
    logger.info(f"Removed {processed} log entries")


@shared_task
def clean_up():
    engine = import_module(settings.SESSION_ENGINE)
    engine.SessionStore.clear_expired()


@shared_task
def clear_tokens():
    clear_expired()
