from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from moneybirdsynchronization import services
from moneybirdsynchronization.models import MoneybirdProject


class Command(BaseCommand):
    """Import the active Moneybird projects, so they can be selected as cost centres."""

    def handle(self, *args, **options):
        if not settings.MONEYBIRD_SYNC_ENABLED:
            raise CommandError(
                "Moneybird synchronization is disabled: set MONEYBIRD_ADMINISTRATION_ID "
                "and MONEYBIRD_API_KEY."
            )
        services.import_projects()
        active = MoneybirdProject.objects.filter(active=True).count()
        inactive = MoneybirdProject.objects.filter(active=False).count()
        self.stdout.write(
            f"There are now {active} active and {inactive} inactive Moneybird projects."
        )
