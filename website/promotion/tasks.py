from celery import shared_task

from promotion import emails


@shared_task
def promo_update_weekly(self):
    emails.send_weekly_overview()
