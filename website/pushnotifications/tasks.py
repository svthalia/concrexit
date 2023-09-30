import logging
from datetime import timedelta

from django.utils import timezone

from celery import shared_task

from pushnotifications.models import ScheduledMessage

logger = logging.getLogger(__name__)


@shared_task
def send_scheduled_messages():
    """Send a scheduled push notifications."""
    interval = int(120)
    now = timezone.now()

    logger.info("Start sending scheduled notifications")

    before_time = timezone.now() + timedelta(seconds=interval / 2)
    messages = ScheduledMessage.objects.filter(sent__isnull=True, time__lte=before_time)

    for message in messages:
        if (timezone.now() - now).seconds < interval:
            logger.info("Sending push notification %d", message.pk)
            message.executed = timezone.now()
            message.send()
