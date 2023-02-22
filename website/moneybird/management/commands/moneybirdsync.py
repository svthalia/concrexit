from django.core.management.base import BaseCommand

from moneybird.synchronization import synchronize


class Command(BaseCommand):
    help = "Synchronize with Moneybird"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Perform a full sync without using already stored versions",
        )

    def handle(self, *args, **options):
        synchronize(full_sync=options["full"])
        self.stdout.write(
            self.style.SUCCESS("Successfully synchronized with Moneybird")
        )
