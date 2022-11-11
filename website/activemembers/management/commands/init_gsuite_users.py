"""Initialise G Suite users management command."""
import logging

from django.core.management.base import BaseCommand

from googleapiclient.errors import HttpError

from activemembers import emails
from activemembers.gsuite import GSuiteUserService
from members.models import Member

logger = logging.getLogger(__name__)
sync_service = GSuiteUserService()


class Command(BaseCommand):
    """This command allows you to initialise a GSuite organisation with accounts for all members that are staff."""

    def handle(self, *args, **options):
        """Sync all accounts."""
        for member in Member.objects.filter(is_staff=True):
            try:
                email, password = sync_service.create_user(member)
                emails.send_gsuite_welcome_message(member, email, password)
            except HttpError as e:
                logger.error("User %s could not be created: %s", member.username, e)
