from django.apps import apps
from django.core.management.base import BaseCommand


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
        for app in apps.get_app_configs():
            if hasattr(app, "data_minimization_methods"):
                data_minimization_methods = app.data_minimization_methods()
                for data_type in data_minimization_methods.keys():
                    method = data_minimization_methods[data_type]
                    processed = method(options["dry-run"])
                    for p in processed:
                        self.stdout.write(f"Removed {data_type} data for {p}")
