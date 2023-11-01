from django.core.management.base import BaseCommand

from promotion import emails


class Command(BaseCommand):
    """Send a daily overview of promotion that has to be published."""

    def handle(self, *args, **options):
        emails.send_daily_update_overview()
