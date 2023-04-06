"""The signals checked by the moneybrid synchronization package."""
import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_delete

from moneybirdsynchronization import services
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.emails import send_sync_error

from members.models import Member, Profile
from payments.signals import processed_batch
from utils.models.signals import suspendingreceiver

User = get_user_model()


@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the profile is saved."""
    try:
        if instance.is_minimized:
            services.delete_contact(Member.objects.get(profile=instance))
        else:
            services.create_or_update_contact(Member.objects.get(profile=instance))
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_delete,
    sender="members.Profile",
)
def post_profile_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the profile is deleted."""
    try:
        services.delete_contact(Member.objects.get(profile=instance))
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


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

    try:
        if instance.profile.is_minimized:
            services.delete_contact(instance)
        else:
            services.create_or_update_contact(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_delete,
    sender=User,
)
def post_user_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the user is deleted."""
    try:
        services.delete_contact(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
)
def post_event_registration_save(sender, instance, **kwargs):
    try:
        if not instance.is_invited or instance.payment_amount == 0:
            # Delete the invoice, because there should be no invoice for this registration
            services.delete_external_invoice(instance)
        else:
            # Create or update the invoice
            services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_delete,
    sender="events.EventRegistration",
)
def post_event_registration_delete(sender, instance, **kwargs):
    try:
        services.delete_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_save,
    sender="pizzas.FoodOrder",
)
def post_food_order_save(sender, instance, **kwargs):
    try:
        services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    pre_delete,
    sender="pizzas.FoodOrder",
)
def pre_food_order_delete(sender, instance, **kwargs):
    try:
        services.delete_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_save,
    sender="registrations.Registration",
)
def post_registration_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for people who have paid for their registration

    try:
        services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_save,
    sender="registrations.Renewal",
)
def post_renewal_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for people who have paid for their registration

    try:
        services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_delete,
    sender="registrations.Registration",
)
def post_registration_delete(sender, instance, **kwargs):
    try:
        services.delete_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_delete,
    sender="registrations.Renewal",
)
def post_renewal_delete(sender, instance, **kwargs):
    try:
        services.delete_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_save,
    sender="payments.Payment",
)
def post_payment_save(sender, instance, **kwargs):
    try:
        services.create_moneybird_payment(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_delete, sender="moneybirdsynchronization.MoneybirdPayment")
def post_payment_delete(sender, instance, **kwargs):
    try:
        services.delete_moneybird_payment(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    post_save,
    sender="sales.Order",
)
def post_order_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for orders that are paid, because we can have quite some phantom orders

    try:
        services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(
    processed_batch,
)
def post_processed_batch(sender, instance, **kwargs):
    try:
        services.process_thalia_pay_batch(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)
