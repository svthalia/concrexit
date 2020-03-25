"""The signals checked by the registrations package"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from registrations import services
from registrations.models import Registration, Renewal


@receiver(post_save, sender=Registration)
def post_registration_save(sender, instance, **kwargs):
    """Process a registration when it is saved"""

    services.process_registration(instance)


@receiver(post_save, sender=Renewal)
def post_renewal_save(sender, instance, **kwargs):
    """Process a renewal when it is saved"""
    print("Registration")
    services.process_renewal(instance)
