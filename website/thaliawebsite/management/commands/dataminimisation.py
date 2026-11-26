from warnings import warn

from django.apps import apps
from django.core.management.base import BaseCommand

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
        # TODO make this actually sensible not just dumb
        for app in apps.get_app_configs():
            try:
                app.execute_data_minimisation()
            except Exception as e:
                warn("Minimization failed:" + str(e))

        count = minimise_logentries_data(options["dry-run"])
        self.stdout.write(f"Removed {count} log entries")
