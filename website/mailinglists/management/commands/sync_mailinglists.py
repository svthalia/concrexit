"""Mailing list syncing management command."""
import logging

from django.core.management.base import BaseCommand

from mailinglists.gsuite import GSuiteSyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """This command can be run periodically to sync the mailinglists available via GSuite."""

    def handle(self, *args, **options):
        """Sync all mailing lists."""
        sync_service = GSuiteSyncService()
        sync_service.sync_mailing_lists()
