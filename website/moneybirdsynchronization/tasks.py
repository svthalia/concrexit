from django.conf import settings

from celery import shared_task

from moneybirdsynchronization import services


@shared_task
def synchronize_moneybird():
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    services.synchronize_moneybird()
