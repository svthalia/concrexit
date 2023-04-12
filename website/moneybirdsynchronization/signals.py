"""The signals checked by the moneybrid synchronization package."""
import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save

from moneybirdsynchronization import services
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.emails import send_sync_error

from members.models import Member, Profile
from payments.models import BankAccount
from payments.signals import processed_batch
from utils.models.signals import suspendingreceiver

User = get_user_model()


@suspendingreceiver(post_save, sender="members.Profile")
def post_profile_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the profile is saved."""
    updated_fields = kwargs.get("update_fields", None)
    if (
        updated_fields is not None
        and "is_minimized" not in updated_fields
        and "address_street" not in updated_fields
        and "address_street2" not in updated_fields
        and "address_postal_code" not in updated_fields
        and "address_city" not in updated_fields
        and "address_country" not in updated_fields
    ):
        return
    try:
        if instance.is_minimized:
            services.delete_contact(Member.objects.get(profile=instance))
        else:
            services.create_or_update_contact(Member.objects.get(profile=instance))
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_delete, sender="members.Profile")
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

    updated_fields = kwargs.get("update_fields", None)
    if (
        updated_fields is not None
        and "first_name" not in updated_fields
        and "last_name" not in updated_fields
        and "email" not in updated_fields
    ):
        # Only update the contact when the name is changed
        return

    try:
        if instance.profile.is_minimized:
            services.delete_contact(instance)
        else:
            services.create_or_update_contact(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_delete, sender=User)
def post_user_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the user is deleted."""
    try:
        services.delete_contact(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_save, sender=BankAccount)
def post_bankaccount_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the bank account is saved."""
    updated_fields = kwargs.get("update_fields", None)
    if (
        updated_fields is not None
        and "owner" not in updated_fields
        and "iban" not in updated_fields
        and "bic" not in updated_fields
        and "initials" not in updated_fields
        and "last_name" not in updated_fields
    ):
        # Only update the contact when the bank account is changed
        return

    member = Member.objects.get(pk=instance.owner.pk)
    try:
        if member.profile.is_minimized:
            services.delete_contact(member)
        else:
            services.create_or_update_contact(member)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_delete, sender=BankAccount)
def post_bankaccount_delete(sender, instance, **kwargs):
    """Update the contact in Moneybird when the bank account is deleted."""
    member = Member.objects.get(pk=instance.owner.pk)
    try:
        services.create_or_update_contact(member)
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
    post_save,
    sender="registrations.Registration",
)
@suspendingreceiver(
    post_save,
    sender="registrations.Renewal",
)
def post_registration_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for people who have paid for their registration

    try:
        services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_save, sender="sales.Order")
def post_order_save(sender, instance, **kwargs):
    if instance.payment is None:
        return  # We only create invoices for orders that are paid, because we can have quite some phantom orders

    try:
        services.create_or_update_external_invoice(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)


@suspendingreceiver(post_delete, sender="registrations.Renewal")
@suspendingreceiver(
    post_delete,
    sender="registrations.Registration",
)
@suspendingreceiver(
    post_delete,
    sender="pizzas.FoodOrder",
)
@suspendingreceiver(
    post_delete,
    sender="events.EventRegistration",
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
    processed_batch,
)
def post_processed_batch(sender, instance, **kwargs):
    try:
        services.process_thalia_pay_batch(instance)
    except Administration.Error as e:
        send_sync_error(e, instance)
        logging.error("Moneybird synchronization error: %s", e)
