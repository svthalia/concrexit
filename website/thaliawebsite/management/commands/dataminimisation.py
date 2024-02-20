from django.core.management.base import BaseCommand

from events import services as events_services
from facedetection import services as facedetection_services
from members import services as members_services
from payments import services as payments_services
from pizzas import services as pizzas_services
from sales import services as sales_services
from utils.snippets import minimise_logentries_data


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
            self.stdout.write(f"Removed data for {p}")

        processed = events_services.execute_data_minimisation(options["dry-run"])
        for p in processed:
            self.stdout.write(f"Removed registration information for {p}")

        processed = payments_services.execute_data_minimisation(options["dry-run"])
        for p in processed:
            self.stdout.write(f"Removed payments information for {p}")

        processed = pizzas_services.execute_data_minimisation(options["dry-run"])
        for p in processed:
            self.stdout.write(f"Removed food events information for {p}")

        processed = sales_services.execute_data_minimisation(options["dry-run"])
        for p in processed:
            self.stdout.write(f"Removed sales orders for {p}")

        processed = facedetection_services.execute_data_minimisation(options["dry-run"])
        for p in processed:
            self.stdout.write(f"Removed reference faces: {p}")

        count = minimise_logentries_data(options["dry-run"])
        self.stdout.write(f"Removed {count} log entries")
