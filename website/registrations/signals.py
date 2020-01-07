"""The signals checked by the registrations package"""
from django.db.models.signals import post_save

from registrations import services
from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    post_save, sender="payments.Payment", dispatch_uid="registrations_payment_process"
)
def post_payment_save(sender, instance, **kwargs):
    """Process a payment when it is saved"""
    services.process_payment(instance)
