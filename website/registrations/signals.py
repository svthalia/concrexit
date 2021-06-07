"""The signals checked by the registrations package."""
from django.db.models.signals import post_save

from registrations import services
from registrations.models import Registration, Renewal
from utils.models.signals import suspendingreceiver


@suspendingreceiver(post_save, sender=Registration)
@suspendingreceiver(post_save, sender=Renewal)
def post_entry_save(sender, instance, **kwargs):
    """Process an entry when it is saved."""
    try:
        services.process_entry_save(instance)
    except Exception as e:
        # if something goes wrong creating the member,
        # revert the entry: remove the payment
        # and mark the entry again as 'ready for review'
        services.revert_entry(None, instance)
        raise e
