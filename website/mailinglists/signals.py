from django.db.models.signals import pre_save
from django.dispatch import receiver
from googleapiclient.errors import HttpError

from mailinglists.gsuite import GSuiteSyncService
from mailinglists.models import MailingList


@receiver(pre_save, sender='mailinglists.MailingList')
def pre_mailinglist_save(instance, **kwargs):
    sync_service = GSuiteSyncService()
    group = sync_service.mailinglist_to_group(instance)
    old_list = MailingList.objects.filter(pk=instance.pk).first()
    try:
        if old_list is None:
            sync_service.create_group(group)
        else:
            sync_service.update_group(old_list.name, group)
    except HttpError:
        # Cannot do direct create or update, do full sync for list
        sync_service.sync_mailinglists([group])
