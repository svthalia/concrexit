from celery import shared_task

from payments import services


@shared_task
def revoke_mandates():
    services.revoke_old_mandates()
