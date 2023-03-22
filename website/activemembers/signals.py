"""The signals defined by the activemembers package."""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save

from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

from activemembers import emails
from activemembers.gsuite import GSuiteUserService
from members.models import Member
from utils.models.signals import suspendingreceiver

logger = logging.getLogger(__name__)
sync_service = GSuiteUserService()


@suspendingreceiver(
    pre_save, sender=get_user_model(), dispatch_uid="activemembers_user_save"
)
@suspendingreceiver(pre_save, sender=Member, dispatch_uid="activemembers_member_save")
def pre_member_save(instance, **kwargs):
    if not settings.GSUITE_MEMBERS_AUTOSYNC:
        return

    existing_member = Member.objects.filter(pk=instance.pk).first()
    if not existing_member:
        return

    try:
        if not existing_member.is_staff and instance.is_staff:
            email, password = sync_service.create_user(instance)
            emails.send_gsuite_welcome_message(instance, email, password)
        elif existing_member.is_staff and not instance.is_staff:
            sync_service.suspend_user(instance.username)
            emails.send_gsuite_suspended_message(instance)
        elif (
            existing_member.is_staff
            and instance.is_staff
            and existing_member.username != instance.username
        ):
            sync_service.update_user(instance, existing_member.username)
    except (HttpError, RefreshError) as e:
        logger.error("Could not update G Suite account: %s", e)
