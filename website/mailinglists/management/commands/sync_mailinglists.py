"""Mailing list syncing management command"""
import logging

from django.core.management.base import BaseCommand

from mailinglists import gsuite

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        """Sync all mailing lists"""
        gsuite.sync_mailinglists()
