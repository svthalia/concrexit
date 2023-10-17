from celery import shared_task

from moneybirdsynchronization import services


@shared_task
def send_mandates_day_late():
    services.send_mandates_late()
