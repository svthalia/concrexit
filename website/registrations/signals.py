from django.db.models.signals import post_save
from django.dispatch import receiver

from registrations import services


@receiver(post_save, sender='payments.Payment',
          dispatch_uid='registrations_payment_process')
def post_payment_save(sender, instance, **kwargs):
    services.process_payment(instance)
