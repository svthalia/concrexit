from django.core.management.base import BaseCommand

from payments import services


class Command(BaseCommand):
    """This command can be executed periodically to revoke mandates that should no longer be valid."""

    def handle(self, *args, **options):
        services.revoke_old_mandates()
