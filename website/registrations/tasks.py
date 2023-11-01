from celery import shared_task

from registrations import services


@shared_task
def minimise_registrations():
    services.execute_data_minimisation()
