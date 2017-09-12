from django.core.management.base import BaseCommand

from partners import emails


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run instead of sending e-mail',
        )

    def handle(self, *args, **options):
        emails.send_vacancy_expiration_notifications(
            bool(options['dry-run']))
