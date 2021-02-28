from django.core.management.base import BaseCommand

from newsletters import models, services


class Command(BaseCommand):
    """This command can be run to create HTML files of newsletters."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-unsent",
            action="store_true",
            dest="include-unsent",
            default=False,
            help="Include newsletters that haven't been sent yet",
        )

    def handle(self, *args, **options):
        for n in models.Newsletter.objects.all():
            if n.sent or options["include-unsent"]:
                services.save_to_disk(n)
