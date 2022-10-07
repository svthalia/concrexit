import logging

from django.conf import settings
from django.db.models.signals import pre_save

from googleapiclient.errors import HttpError

from mailinglists.gsuite import GSuiteSyncService
from mailinglists.models import MailingList
from utils.models.signals import suspendingreceiver

logger = logging.getLogger(__name__)


@suspendingreceiver(pre_save, sender="mailinglists.MailingList")
def pre_mailinglist_save(instance, **kwargs):
    if settings.GSUITE_ADMIN_CREDENTIALS == {}:
        logger.warning(
            "Cannot sync mailinglists because there are no GSuite credentials available"
        )
        return
    sync_service = GSuiteSyncService()
    group = sync_service.mailing_list_to_group(instance)
    old_list = MailingList.objects.filter(pk=instance.pk).first()
    try:
        if old_list is None:
            sync_service.create_group(group)
        else:
            sync_service.update_group(old_list.name, group)
    except HttpError:
        # Cannot do direct create or update, do full sync for list
        sync_service.sync_mailing_lists([group])
