from celery import shared_task

from mailinglists.gsuite import GSuiteSyncService


@shared_task
def sync_mail():
    sync_service = GSuiteSyncService()
    sync_service.sync_mailing_lists()
