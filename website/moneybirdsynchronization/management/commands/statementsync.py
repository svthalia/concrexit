from django.core.management.base import BaseCommand

from moneybirdsynchronization import services


class Command(BaseCommand):
    """This command needs to be executed every day to sync the bookkeeping with MoneyBird."""

    def handle(self, *args, **options):
        services.sync_statements()
