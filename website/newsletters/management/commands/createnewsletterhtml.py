from django.core.management.base import BaseCommand
from django.http import HttpRequest

from newsletters import models, services


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--include-unsent",
            action="store_true",
            dest="include-unsent",
            default=False,
            help="Include newsletters that haven't been sent yet",
        )
        parser.add_argument(
            "server-name",
            help="The server name for the request "
            "to generate the html (typically thalia.nu)",
        )
        parser.add_argument(
            "server-port",
            type=int,
            help="The server port for the request "
            "to generate the html (typically 80)",
        )

    def handle(self, *args, **options):
        request = HttpRequest()
        request.META["SERVER_NAME"] = options["server-name"]
        request.META["SERVER_PORT"] = options["server-port"]
        for n in models.Newsletter.objects.all():
            if n.sent or options["include-unsent"]:
                services.save_to_disk(n, request)
