from celery import shared_task

from . import services


@shared_task
def renew_merchandise_sale_shift():
    services.renew_merchandise_sale_shift()
