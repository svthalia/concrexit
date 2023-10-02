from celery import shared_task

from members import emails


@shared_task
def membership_announcement():
    emails.send_membership_announcement()


@shared_task
def info_request():
    emails.send_information_request()


@shared_task
def expiration_announcement():
    emails.send_expiration_announcement()
