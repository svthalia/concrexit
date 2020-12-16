"""Mailing list syncing management command."""
import logging

from django.core.management.base import BaseCommand

from mailinglists.gsuite import GSuiteSyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Sync all mailing lists."""
        sync_service = GSuiteSyncService()
        sync_service.sync_mailinglists()
