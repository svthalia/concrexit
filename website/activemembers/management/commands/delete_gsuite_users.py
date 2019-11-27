"""Mailing list syncing management command"""
import logging

from django.core.management.base import BaseCommand

from activemembers.gsuite import GSuiteUserService

logger = logging.getLogger(__name__)
sync_service = GSuiteUserService()


class Command(BaseCommand):

    def handle(self, *args, **options):
        """Sync all accounts """
        suspended_users = sync_service.get_suspended_users()
        for user in suspended_users:
            sync_service.delete_user(user['primaryEmail'])
