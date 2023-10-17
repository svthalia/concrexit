from celery import shared_task

from moneybirdsynchronization import services


@shared_task
def sync_contacts_with_outdated_mandates():
    services.sync_contacts_with_outdated_mandates()
