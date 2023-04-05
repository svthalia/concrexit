"""The signals checked by the moneybrid synchronization package."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_delete

from moneybirdsynchronization import services

from members.models import Member, Profile
from sales.models.order import Order
from utils.models.signals import suspendingreceiver

User = get_user_model()


@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the profile is saved."""
    if instance.is_minimized:
        services.delete_contact(Member.objects.get(profile=instance))
    else:
        services.create_or_update_contact(Member.objects.get(profile=instance))


@suspendingreceiver(
    post_delete,
    sender="members.Profile",
)
def post_profile_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the profile is deleted."""
    services.delete_contact(Member.objects.get(profile=instance))


@suspendingreceiver(
    post_save,
    sender=User,
)
def post_user_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the user is saved."""
    try:
        instance.profile
    except Profile.DoesNotExist:
        return

    if instance.profile.is_minimized:
        services.delete_contact(instance)
    else:
        services.create_or_update_contact(instance)


@suspendingreceiver(
    post_delete,
    sender=User,
)
def post_user_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the user is deleted."""
    services.delete_contact(instance)


@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
)
def post_event_registration_save(sender, instance, **kwargs):
    if not instance.is_invited or instance.payment_amount == 0:
        # Delete the invoice, because there should be no invoice for this registration
        services.delete_external_invoice(instance)
    else:
        # Create or update the invoice
        services.create_or_update_external_invoice(instance)

    # try:
    #
    # except Administration.Error:
    #     # TODO
    #     pass


@suspendingreceiver(
    post_delete,
    sender="events.EventRegistration",
)
def post_event_registration_delete(sender, instance, **kwargs):
    services.delete_external_invoice(instance)


@suspendingreceiver(
    post_save,
    sender="pizzas.FoodOrder",
)
def post_food_order_save(sender, instance, **kwargs):
    services.create_or_update_external_invoice(instance)


@suspendingreceiver(
    pre_delete,
    sender="pizzas.FoodOrder",
)
def pre_food_order_delete(sender, instance, **kwargs):
    services.delete_external_invoice(instance)


@suspendingreceiver(
    post_save,
    sender="registrations.Registration",
)
def post_registration_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for people who have paid for their registration

    services.create_or_update_external_invoice(instance)


@suspendingreceiver(
    post_save,
    sender="registrations.Renewal",
)
def post_renewal_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for people who have paid for their registration

    services.create_or_update_external_invoice(instance)


@suspendingreceiver(
    post_delete,
    sender="registrations.Registration",
)
def post_registration_delete(sender, instance, **kwargs):
    services.delete_external_invoice(instance)


@suspendingreceiver(
    post_delete,
    sender="registrations.Renewal",
)
def post_renewal_delete(sender, instance, **kwargs):
    services.delete_external_invoice(instance)


@suspendingreceiver(
    post_save,
    sender="payments.Payment",
)
def post_payment_save(sender, instance, **kwargs):
    services.create_moneybird_payment(instance)


@suspendingreceiver(post_delete, sender="moneybirdsynchronization.MoneybirdPayment")
def post_payment_delete(sender, instance, **kwargs):
    services.delete_moneybird_payment(instance)


@suspendingreceiver(
    post_save,
    sender="sales.Shift",
)
def post_shift_save(sender, instance, **kwargs):
    # TODO we can also do this for each order when they are paid

    if not instance.locked:
        return  # We only create invoices for orders in locked shifts,
        # because syncing every order that is created real-time is too much work.

    orders = Order.objects.filter(shift=instance)
    for order in orders:
        services.create_or_update_external_invoice(order)


# @suspendingreceiver(
#     processed_batch,
# )
# def post_processed_batch(sender, instance, **kwargs):
#     if (
#         instance.pushed_thaliapay_batch is not None
#         and instance.pushed_thaliapay_batch.processed
#     ):
#         return
#
#     if instance.pushed_thaliapay_batch is None:
#         PushedThaliaPayBatch.objects.create(batch=instance)
#     else:
#         services.push_thaliapay_batch(instance)
