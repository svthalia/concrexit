from celery import shared_task

from members import emails


@shared_task
def info_request():
    emails.send_information_request()


@shared_task
def expiration_announcement():
    emails.send_expiration_announcement()


@shared_task
def expiration_warning():
    emails.send_expiration_study_long()


@shared_task
def expiration_reminder():
    emails.send_expiration_study_long_reminder()
