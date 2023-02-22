from django.core.management.base import BaseCommand

from moneybird.webhooks.register import delete_webhook


class Command(BaseCommand):
    help = "Delete webhook at Moneybird"

    def add_arguments(self, parser):
        parser.add_argument("webhook_id", nargs="+", type=int)

    def handle(self, *args, **options):
        webhook_id = options["webhook_id"]
        delete_webhook(webhook_id)
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted webhook {webhook_id}.")
        )
