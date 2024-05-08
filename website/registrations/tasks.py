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
    # delete entries w updated_at 1 month ago and created_at 3m ago
    # notify (and update updated_at) entries w updated_at 1 month ago

    Registration.objects.filter(
        updated_at__lt=timezone.now() - timedelta(days=30),
        created_at__lt=timezone.now() - timedelta(days=90),
    ).delete()
    Renewal.objects.filter(
        updated_at__lt=timezone.now() - timedelta(days=30),
        created_at__lt=timezone.now() - timedelta(days=90),
    ).delete()

    for registration in Registration.objects.filter(
        updated_at__lt=timezone.now() - timedelta(days=30)
    ):
        # send email
        emails.send_reminder_open_registration(registration)
        registration.updated_at = timezone.now()
        registration.save()
