from django.core.management.base import BaseCommand

from promotion import emails


class Command(BaseCommand):
    """Send a weekly overview of open promotion requests."""

    def handle(self, *args, **options):
        emails.send_weekly_overview()
