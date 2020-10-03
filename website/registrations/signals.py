"""The signals checked by the registrations package"""
from django.db.models.signals import post_save

from registrations import services
from registrations.models import Registration, Renewal
from utils.models.signals import suspendingreceiver


@suspendingreceiver(post_save, sender=Registration)
@suspendingreceiver(post_save, sender=Renewal)
def post_entry_save(sender, instance, **kwargs):
    """Process an entry when it is saved"""
    services.process_entry_save(instance)
