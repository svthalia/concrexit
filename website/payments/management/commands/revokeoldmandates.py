from django.core.management.base import BaseCommand

from payments import services


class Command(BaseCommand):
    def handle(self, *args, **options):
        services.revoke_old_mandates()
