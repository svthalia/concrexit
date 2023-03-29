from django.core.management.base import BaseCommand
from moneybirdsynchronization import services


class Command(BaseCommand):
    """This command can be executed periodically to sync the contacts with MoneyBird."""

    def handle(self, *args, **options):
        services.sync_contacts()
