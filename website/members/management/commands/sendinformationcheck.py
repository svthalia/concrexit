from django.core.management.base import BaseCommand

from members import emails


class Command(BaseCommand):
    """This command can be executed once a year to send emails to members to check if the information we have is still correct."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of sending e-mail",
        )

    def handle(self, *args, **options):
        emails.send_information_request(bool(options["dry-run"]))
