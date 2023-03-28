"""The signals checked by the moneybrid synchronization package."""
from django.db.models.signals import pre_save, post_save, pre_delete
from django.template.defaultfilters import date
import logging

from utils.models.signals import suspendingreceiver

from members.models import Member
from moneybirdsynchronization.models import Contact
from moneybirdsynchronization.administration import HttpsAdministration, Administration
from moneybirdsynchronization.services import MoneybirdAPIService
from moneybirdsynchronization import services
from payments.models import Payment
from sales.models.order import Order
from events.models.event import Event
from thaliawebsite import settings

@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_save(sender, instance, **kwargs):
    """Update contact on profile creation."""
    services.update_contact(Contact.objects.get_or_create(member=instance)[0])


@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_delete(sender, instance, **kwargs):
    """Delete contact on profile deletion."""
    if kwargs["update_fields"].__contains__("is_minimized") is False:
        return
    if instance.is_minimized is False:
        return
    
    services.delete_contact(instance)


@suspendingreceiver(
    post_save,
    sender="auth.User",
)
def post_user_save(sender, instance, **kwargs):
    """Update contact on user creation."""
    services.update_contact(instance)


@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
)
def post_event_registration_payment(sender, instance, **kwargs):
    """ Create external invoice on payment creation."""
    if instance.payment is None:
        return
    if instance.payment.moneybird_invoice_id is not None:
        return
    
    services.register_event_registration_payment(instance)


@suspendingreceiver(
    post_save,
    sender="sales.Shift",
)
def post_shift_save(sender, instance, **kwargs):
    if not instance.locked:
        return
    
    orders = Order.objects.filter(shift=instance)
    if len(orders) == 0:
        return
    if orders[0].payment.moneybird_invoice_id is not None:
        return
    services.register_shift_payments(orders, instance)


@suspendingreceiver(
    post_save,
    sender="pizzas.FoodOrder",
)
def post_food_order_save(sender, instance, **kwargs):
    """ Create external invoice on payment creation."""
    if instance.payment is None:
        return
    if instance.payment.moneybird_invoice_id is not None:
        return
    
    services.register_food_order_payment(instance)


@suspendingreceiver(
    post_save,
    sender="registrations.Registration",
)
def post_entry_save(sender, instance, **kwargs):
    """ Create external invoice on payment creation."""
    if instance.payment is None:
        return
    if instance.payment.moneybird_invoice_id is not None:
        return
    
    services.register_contribution_payment(instance)


@suspendingreceiver(
    post_save,
    sender="registrations.Renewal",
)
def post_renewal_save(sender, instance, **kwargs):
    """ Create external invoice on payment creation."""
    if instance.payment is None:
        return
    if instance.payment.moneybird_invoice_id is not None:
        return
    
    services.register_contribution_payment(instance)


@suspendingreceiver(
    pre_delete,
    sender="payments.Payment",
)
def pre_payment_delete(sender, instance, **kwargs):
    """ Delete external invoice on payment deletion."""
    if instance.moneybird_invoice_id is None:
        return

    services.delete_payment(instance)


@suspendingreceiver(
    pre_save,
    sender="payments.Batch",
)
def post_batch_save(sender, instance, **kwargs):
    if kwargs["update_fields"] is None:
        return
    
    if kwargs["update_fields"].__contains__("processed") is False:
        return
    
    services.push_thaliapay_batch(instance)