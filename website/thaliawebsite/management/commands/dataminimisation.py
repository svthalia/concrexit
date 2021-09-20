from django.core.management.base import BaseCommand

from members import services as members_services
from events import services as events_services


class Command(BaseCommand):
    """This command can be executed periodically to minimise the user information in our database."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of saving data",
        )

    def handle(self, *args, **options):
        processed = members_services.execute_data_minimisation(options["dry-run"])
        for p in processed:
            self.stdout.write("Removed data for {}".format(p))

        processed = events_services.execute_data_minimization(options["dry-run"])
        for p in processed:
            self.stdout.write("Removed registration information for {}".format(p))
