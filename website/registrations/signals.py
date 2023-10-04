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
        try:
            services.complete_registration(instance)
        except Exception as e:
            # If something goes wrong completing the registration, log it and revert
            # the registration: delete the payment and put it back to review.
            logger.exception(f"Error completing registration: {e}")
            services.revert_registration(instance)


@suspendingreceiver(post_save, sender=Renewal)
def complete_paid_renewal(sender, instance: Renewal, **kwargs):
    """Complete a renewal once a payment for it is made."""
    if instance.status == Renewal.STATUS_ACCEPTED and instance.payment is not None:
        try:
            services.complete_renewal(instance)
        except Exception as e:
            # If something goes wrong completing the renewal, log it and revert
            # the renewal: delete the payment and put it back to review.
            logger.exception(f"Error completing renewal: {e}")
            services.revert_renewal(instance)
