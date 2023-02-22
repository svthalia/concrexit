from django.core.management.base import BaseCommand

from moneybird.webhooks.register import create_webhook


class Command(BaseCommand):
    help = "Register webhook at Moneybird"

    def handle(self, *args, **options):
        webhook = create_webhook()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully registered webhook to {webhook['url']} at Moneybird with id {webhook['id']} and token {webhook['token']}."
            )
        )
