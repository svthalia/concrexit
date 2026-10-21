from django.core.management import BaseCommand

from registrations import apps


class Command(BaseCommand):
    """This command needs to be executed periodically to remove all data that is no longer necessary and can be removed."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of saving data",
        )

    def handle(self, *args, **options):
        apps.RegistrationsConfig.execute_data_minimisation(options["dry-run"])
