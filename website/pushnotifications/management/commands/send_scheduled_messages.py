import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from pushnotifications.models import ScheduledMessage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of sending notifications",
        )
        parser.add_argument(
            "--interval",
            dest="interval",
            default=300,
            help="Interval in seconds in which this task is executed",
        )

    def handle(self, *args, **options):
        """Send a scheduled push notifications."""
        interval = int(options["interval"])
        now = timezone.now()

        logger.info("Start sending scheduled notifications")

        before_time = timezone.now() + timedelta(seconds=interval / 2)
        messages = ScheduledMessage.objects.filter(
            sent__isnull=True, time__lte=before_time
        )

        for message in messages:
            if (timezone.now() - now).seconds < interval:
                logger.info("Sending push notification %d", message.pk)
                message.executed = timezone.now()
                message.send(dry_run=bool(options["dry-run"]))
