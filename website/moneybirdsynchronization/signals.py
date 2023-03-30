"""The signals checked by the moneybrid synchronization package."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete

from moneybirdsynchronization import services
from moneybirdsynchronization.models import MoneybirdContact, PushedThaliaPayBatch

from members.models import Member
from sales.models.order import Order
from utils.models.signals import suspendingreceiver

User = get_user_model()


@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_save(sender, instance, **kwargs):
    services.update_contact(MoneybirdContact.objects.get_or_create(member=instance)[0])


@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_delete(sender, instance, **kwargs):
    if "is_minimized" in kwargs["update_fields"]:
        return
    if instance.is_minimized is False:
        return

    services.delete_contact(Member.objects.get(profile=instance))


@suspendingreceiver(
    post_save,
    sender=User,
)
def post_user_save(sender, instance, **kwargs):
    services.update_contact(instance)


@suspendingreceiver(
    post_save,
    sender="payments.Payment",
)
def post_payment_save(sender, instance, **kwargs):
    if instance.moneybird_external_invoice is not None:
        return

    services.create_external_invoice(instance)


@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
)
def post_event_registration_payment(sender, instance, **kwargs):
    if instance.payment is None:
        return
    if instance.payment.moneybird_external_invoice.moneybird_invoice_id is not None:
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
    if instance.moneybird_external_invoice.moneybird_invoice_id is None:
        return

    services.delete_payment(instance)


@suspendingreceiver(
    post_save,
    sender="payments.Batch",
)
def post_batch_save(sender, instance, **kwargs):
    if (
        instance.pushed_thaliapay_batch is not None
        and instance.pushed_thaliapay_batch.processed
    ):
        return
    if instance.pushed_thaliapay_batch is None:
        PushedThaliaPayBatch.objects.create(batch=instance)
    else:
        services.push_thaliapay_batch(instance)
