"""The signals checked by the moneybrid synchronization package."""
import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save

from members.models import Member, Profile
from moneybirdsynchronization import services
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.emails import send_sync_error
from moneybirdsynchronization.models import MoneybirdExternalInvoice
from payments.models import BankAccount
from payments.signals import processed_batch
from utils.models.signals import suspendingreceiver

logger = logging.getLogger(__name__)
User = get_user_model()


@suspendingreceiver(post_save, sender="members.Profile")
def post_profile_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the profile is saved."""
    updated_fields = kwargs.get("update_fields", None)
    if updated_fields is not None and not any(
        field in updated_fields
        for field in [
            "is_minimized",
            "address_street",
            "address_street2",
            "address_postal_code",
            "address_city",
            "address_country",
        ]
    ):
        return

    if not instance.user.first_name or not instance.user.last_name:
        return

    try:
        if instance.is_minimized:
            services.delete_contact(instance.user)
        else:
            services.create_or_update_contact(instance.user)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance.user)


@suspendingreceiver(post_delete, sender="members.Profile")
def post_profile_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the profile is deleted."""
    try:
        services.delete_contact(instance.user)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance.user)


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
    if updated_fields is not None and not any(
        field in updated_fields for field in ["first_name", "last_name", "email"]
    ):
        # Only update the contact when the name is changed
        return

    try:
        if instance.profile.is_minimized:
            services.delete_contact(instance)
        else:
            services.create_or_update_contact(instance)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance)


@suspendingreceiver(post_delete, sender=User)
def post_user_delete(sender, instance, **kwargs):
    """Delete the contact in Moneybird when the user is deleted."""
    try:
        services.delete_contact(instance)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance)


@suspendingreceiver(post_save, sender=BankAccount)
def post_bank_account_save(sender, instance, **kwargs):
    """Update the contact in Moneybird when the bank account is saved."""
    updated_fields = kwargs.get("update_fields", None)
    if updated_fields is not None and not any(
        field in updated_fields
        for field in ["owner", "iban", "bic", "initials", "last_name"]
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
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance)


@suspendingreceiver(post_delete, sender=BankAccount)
def post_bank_account_delete(sender, instance, **kwargs):
    """Update the contact in Moneybird when the bank account is deleted."""
    member = Member.objects.get(pk=instance.owner.pk)
    try:
        services.create_or_update_contact(member)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance)


@suspendingreceiver(
    post_save,
    sender="registrations.Renewal",
    dispatch_uid="mark_renewal_invoice_outdated",
)
@suspendingreceiver(
    post_save,
    sender="registrations.Registration",
    dispatch_uid="mark_registration_invoice_outdated",
)
@suspendingreceiver(
    post_save, sender="pizzas.FoodOrder", dispatch_uid="mark_foodorder_invoice_outdated"
)
@suspendingreceiver(
    post_save, sender="sales.Order", dispatch_uid="mark_salesorder_invoice_outdated"
)
@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
    dispatch_uid="mark_eventregistration_invoice_outdated",
)
def mark_invoice_outdated(sender, instance, **kwargs):
    """Mark the invoice as outdated if it exists, so that it will be resynchronized."""
    invoice = MoneybirdExternalInvoice.get_for_object(instance)
    if invoice and not invoice.needs_synchronization:
        invoice.needs_synchronization = True
        invoice.save()


@suspendingreceiver(post_delete, sender="registrations.Renewal")
@suspendingreceiver(post_delete, sender="registrations.Registration")
@suspendingreceiver(post_delete, sender="pizzas.FoodOrder")
@suspendingreceiver(post_delete, sender="events.EventRegistration")
@suspendingreceiver(post_delete, sender="sales.Order")
def post_renewal_delete(sender, instance, **kwargs):
    """When a payable is deleted, other than during data minimisation, delete the invoice.

    When objects are deleted for data minimisation, we don't want to delete the
    Moneybird invoice as well, because we are obligated to store those for 7 years.
    """
    # During data minimisation, deletions are marked with a flag. This is currently
    # the case only for registrations and renewals. The other payables are not deleted
    # for data minimisation, but bulk-updated to remove personally identifiable
    # information. Those bulk updates do not trigger post_save signals.
    if getattr(instance, "__deleting_for_dataminimisation", False):
        return

    invoice = MoneybirdExternalInvoice.get_for_object(instance)
    if invoice:
        invoice.needs_deletion = True
        invoice.save()


@suspendingreceiver(post_delete, sender="moneybirdsynchronization.MoneybirdPayment")
def post_payment_delete(sender, instance, **kwargs):
    try:
        services.delete_moneybird_payment(instance)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance)


@suspendingreceiver(
    processed_batch,
)
def post_processed_batch(sender, instance, **kwargs):
    try:
        services.process_thalia_pay_batch(instance)
    except Administration.Error as e:
        logger.exception("Moneybird synchronization error: %s", e)
        send_sync_error(e, instance)
