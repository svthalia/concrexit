from django.core.management.base import BaseCommand

from moneybird.webhooks.register import get_webhooks


class Command(BaseCommand):
    help = "Check out the webhooks registered at Moneybird"

    def handle(self, *args, **options):
        webhooks = get_webhooks()
        for webhook in webhooks:
            self.stdout.write(
                f"Webhook {webhook['id']} at {webhook['url']} with token {webhook['token']}."
            )
