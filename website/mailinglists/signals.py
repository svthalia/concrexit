from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from mailinglists.gsuite import mailinglist_to_group, sync_mailinglists


@receiver(post_save, sender='mailinglists.MailingList')
def post_mailinglist_save(instance, **kwargs):
    sync_mailinglists([mailinglist_to_group(instance)])


@receiver(post_delete, sender='mailinglists.MailingList')
def post_mailinglist_delete(instance, **kwargs):
    sync_mailinglists([mailinglist_to_group(instance)])
