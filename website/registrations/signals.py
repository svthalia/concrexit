"""The signals checked by the registrations package"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from registrations import services


@receiver(post_save, sender='payments.Payment',
          dispatch_uid='registrations_payment_process')
def post_payment_save(sender, instance, **kwargs):
    """Process a payment when it is saved"""
    services.process_payment(instance)
