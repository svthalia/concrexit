from celery import shared_task

from . import services


@shared_task
def renew_merchandise_sale_shift():
    services.lock_merchandise_sale_shift()
    services.create_daily_merchandise_sale_shift()
