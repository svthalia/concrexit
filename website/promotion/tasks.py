from celery import shared_task

from promotion import emails


@shared_task
def promo_update_weekly():
    emails.send_weekly_overview()


@shared_task
def promo_update_daily():
    emails.send_daily_overview()
