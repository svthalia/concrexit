from django.core.management.base import BaseCommand

from partners import emails


class Command(BaseCommand):
    """Command class for sendvacancyexpirationnotification command."""

    def add_arguments(self, parser):
        """Add --dry-run argument to command."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run instead of sending e-mail',
        )

    def handle(self, *args, **options):
        """Call the function to handle the sending of emails."""
        emails.send_vacancy_expiration_notifications(
            bool(options['dry-run']))
