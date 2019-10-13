from django.db.models.signals import pre_save, \
    pre_delete
from django.dispatch import receiver
from googleapiclient.errors import HttpError

from mailinglists.gsuite import (mailinglist_to_group, sync_mailinglists,
                                 update_group, create_group)
from mailinglists.models import MailingList


@receiver(pre_save, sender='mailinglists.MailingList')
def pre_mailinglist_save(instance, **kwargs):
    group = mailinglist_to_group(instance)
    old_list = MailingList.objects.filter(pk=instance.pk).first()
    try:
        if old_list is None:
            create_group(group)
        else:
            update_group(old_list.name, group)
    except HttpError:
        # Cannot do direct create or update, do full sync for list
        sync_mailinglists([group])


@receiver(pre_delete, sender='mailinglists.MailingList')
def pre_mailinglist_delete(instance, **kwargs):
    sync_mailinglists([mailinglist_to_group(instance)])
