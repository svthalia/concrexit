from datetime import timedelta

from django.utils import timezone

from celery import shared_task

from registrations import emails

from . import services
from .models import Registration, Renewal


@shared_task
def minimise_registrations():
    services.execute_data_minimisation()


@shared_task
def notify_old_entries():
    """Delete very old entries and send a reminder to board for less old entries."""
    Registration.objects.exclude(
        status__in=(Registration.STATUS_COMPLETED, Registration.STATUS_REJECTED)
    ).filter(
        payment=None,
        updated_at__lt=timezone.now() - timedelta(days=30),
        created_at__lt=timezone.now() - timedelta(days=90),
    ).delete()
    Renewal.objects.exclude(
        status__in=(Renewal.STATUS_COMPLETED, Renewal.STATUS_REJECTED)
    ).filter(
        payment=None,
        updated_at__lt=timezone.now() - timedelta(days=30),
        created_at__lt=timezone.now() - timedelta(days=90),
    ).delete()

    for registration in Registration.objects.exclude(
        status__in=(Registration.STATUS_COMPLETED, Registration.STATUS_REJECTED)
    ).filter(payment=None, updated_at__lt=timezone.now() - timedelta(days=30)):
        emails.send_reminder_open_registration(registration)
        registration.updated_at = timezone.now()
        registration.save()

    for renewal in Renewal.objects.exclude(
        status__in=(Renewal.STATUS_COMPLETED, Renewal.STATUS_REJECTED)
    ).filter(payment=None, updated_at__lt=timezone.now() - timedelta(days=30)):
        emails.send_reminder_open_renewal(renewal)
        renewal.updated_at = timezone.now()
        renewal.save()
