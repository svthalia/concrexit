import logging

from django.db.models.signals import post_save

from registrations import services
from registrations.models import Registration, Renewal
from utils.models.signals import suspendingreceiver

logger = logging.getLogger(__name__)


@suspendingreceiver(post_save, sender=Registration)
def complete_paid_registration(sender, instance: Registration, **kwargs):
    """Complete a registration once a payment for it is made."""
    if instance.status == Registration.STATUS_ACCEPTED and instance.payment is not None:
        services.complete_registration(instance)
        # If something goes wrong completing the registration, the exception is propagated.
        # Creating the payment will in turn fail, leaving the registration accepted but not paid.


@suspendingreceiver(post_save, sender=Renewal)
def complete_paid_renewal(sender, instance: Renewal, **kwargs):
    """Complete a renewal once a payment for it is made."""
    if instance.status == Renewal.STATUS_ACCEPTED and instance.payment is not None:
        services.complete_renewal(instance)
        # If something goes wrong completing the renewal, the exception is propagated.
        # Creating the payment will in turn fail, leaving the renewal accepted but not paid.
