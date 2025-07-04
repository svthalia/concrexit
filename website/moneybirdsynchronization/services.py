import logging

from django.conf import settings
from django.contrib.admin.utils import model_ngettext
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import CharField, Exists, F, OuterRef, Q, Subquery
from django.db.models.functions import Cast
from django.utils import timezone

from events.models import EventRegistration
from members.models import Member
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.emails import send_sync_error
from moneybirdsynchronization.models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
    MoneybirdReceipt,
    financial_account_id_for_payment_type,
)
from moneybirdsynchronization.moneybird import get_moneybird_api_service
from payments.models import BankAccount, Payment
from pizzas.models import FoodOrder
from registrations.models import Registration, Renewal
from reimbursements.models import Reimbursement
from sales.models.order import Order

logger = logging.getLogger(__name__)


def create_or_update_contact(member: Member):
    """Push a Django user/member to Moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return None

    moneybird_contact, _ = MoneybirdContact.objects.get_or_create(member=member)

    moneybird = get_moneybird_api_service()

    if moneybird_contact.moneybird_id is None:
        # Push contact to moneybird. This may fail with 422 when moneybird rejects an
        # email address. In that case, we try once more leaving out the email address,
        # as moneybird does not require that we set one at all.
        try:
            response = moneybird.create_contact(moneybird_contact.to_moneybird())
        except Administration.InvalidData:
            logger.info("Retrying to create contact without email...")
            contact = moneybird_contact.to_moneybird()
            del contact["contact"]["send_invoices_to_email"]
            response = moneybird.create_contact(contact)

        moneybird_contact.moneybird_id = response["id"]
    else:
        # Update the contact data (right now we always do this, but we could use the version to check if it's needed).
        try:
            response = moneybird.update_contact(
                moneybird_contact.moneybird_id, moneybird_contact.to_moneybird()
            )
        except Administration.InvalidData:
            logger.info("Retrying to update contact without email...")
            contact = moneybird_contact.to_moneybird()
            del contact["contact"]["send_invoices_to_email"]
            response = moneybird.update_contact(moneybird_contact.moneybird_id, contact)

    moneybird_contact.moneybird_sepa_mandate_id = response["sepa_mandate_id"] or None
    moneybird_contact.needs_synchronization = False
    moneybird_contact.save()
    return moneybird_contact


def delete_contact(contact: MoneybirdContact):
    """Delete or archive a contact on Moneybird, and delete our record of it."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    if contact.moneybird_id is None:
        contact.delete()
        return

    moneybird = get_moneybird_api_service()
    try:
        moneybird.delete_contact(contact.moneybird_id)
        contact.delete()
    except Administration.InvalidData as e:
        if e.status_code == 400 and e.description == "Contact can not be archived":
            # Contact is most likely already archived, so we can delete it.
            logger.warning(
                "Contact %s for member %s could not be archived.",
                contact.moneybird_id,
                contact.member,
            )
            contact.delete()
        else:
            raise


def create_or_update_external_invoice(obj):
    """Create an external sales invoice on Moneybird for a payable object."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return None

    external_invoice = MoneybirdExternalInvoice.get_for_object(obj)
    if external_invoice is None:
        external_invoice = MoneybirdExternalInvoice.create_for_object(obj)

    moneybird = get_moneybird_api_service()

    if external_invoice.moneybird_invoice_id:
        moneybird.update_external_sales_invoice(
            external_invoice.moneybird_invoice_id, external_invoice.to_moneybird()
        )
    else:
        response = moneybird.create_external_sales_invoice(
            external_invoice.to_moneybird()
        )
        external_invoice.moneybird_invoice_id = response["id"]
        external_invoice.moneybird_details_attribute_id = response["details"][0]["id"]

    if external_invoice.payable.payment is not None:
        # Mark the invoice as paid if the payable is paid as well
        try:
            moneybird_payment = MoneybirdPayment.objects.get(
                payment=external_invoice.payable.payment
            )
        except MoneybirdPayment.DoesNotExist:
            moneybird_payment = None

        if (
            moneybird_payment is not None
            and moneybird_payment.moneybird_financial_mutation_id is not None
        ):
            mutation_info = moneybird.get_financial_mutation_info(
                external_invoice.payable.payment.moneybird_payment.moneybird_financial_mutation_id
            )
            if not any(
                x["invoice_type"] == "ExternalSalesInvoice"
                and x["invoice_id"] == external_invoice.moneybird_invoice_id
                for x in mutation_info["payments"]
            ):
                # If the payment itself also already exists in a financial mutation
                # and is not yet linked to the booking, link it
                moneybird.link_mutation_to_booking(
                    mutation_id=int(
                        external_invoice.payable.payment.moneybird_payment.moneybird_financial_mutation_id
                    ),
                    booking_id=int(external_invoice.moneybird_invoice_id),
                    price_base=str(external_invoice.payable.payment_amount),
                )
        else:
            # Otherwise, mark it as paid without linking to an actual payment
            # (announcing that in the future, a mutation should become available)
            moneybird.register_external_invoice_payment(
                external_invoice.moneybird_invoice_id,
                {
                    "payment": {
                        "payment_date": external_invoice.payable.payment.created_at.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "price": str(external_invoice.payable.payment_amount),
                        "financial_account_id": financial_account_id_for_payment_type(
                            external_invoice.payable.payment.type
                        ),
                    }
                },
            )

    # Mark the invoice as not outdated anymore only after everything has succeeded.
    external_invoice.needs_synchronization = False
    external_invoice.save()

    return external_invoice


def delete_external_invoice(obj):
    """Delete an external invoice from Moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    external_invoice = MoneybirdExternalInvoice.get_for_object(obj)
    if external_invoice is None:
        return

    if external_invoice.moneybird_invoice_id is None:
        external_invoice.delete()
        return

    moneybird = get_moneybird_api_service()
    try:
        moneybird.delete_external_sales_invoice(external_invoice.moneybird_invoice_id)
    except Administration.NotFound:
        # The invoice has probably been removed manually from moneybird.
        # We can assume it no longer exists there, but still, this should not happen
        # too often, so we log it.
        logger.warning(
            "Tried to delete non-existing invoice %s with moneybird ID %s",
            external_invoice,
            external_invoice.moneybird_invoice_id,
        )
    finally:
        external_invoice.delete()


def create_receipt(reimbursement: Reimbursement):
    """Create a receipt on Moneybird for a Reimbursement object."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    if reimbursement.verdict != Reimbursement.Verdict.APPROVED:
        return

    moneybird_receipt, _ = MoneybirdReceipt.objects.get_or_create(
        reimbursement=reimbursement
    )

    moneybird = get_moneybird_api_service()

    if moneybird_receipt.moneybird_receipt_id is None:
        response = moneybird.create_receipt(moneybird_receipt.to_moneybird())
        moneybird_receipt.moneybird_receipt_id = response["id"]
        moneybird_receipt.save()

    if not moneybird_receipt.moneybird_attachment_is_uploaded:
        moneybird.add_receipt_attachment(
            moneybird_receipt.moneybird_receipt_id,
            reimbursement.receipt,
        )
        moneybird_receipt.moneybird_attachment_is_uploaded = True
        moneybird_receipt.save()

    return moneybird_receipt


def synchronize_moneybird():
    """Perform all synchronization to moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    logger.info("Starting moneybird synchronization.")

    _sync_contacts()

    # Push all payments to moneybird. This needs to be done before the invoices,
    # as creating/updating invoices will link the payments to the invoices if they
    # already exist on moneybird.
    _sync_moneybird_payments()

    # Delete invoices and receipts that have been marked for deletion.
    _delete_invoices()

    # Resynchronize outdated invoices.
    _sync_outdated_invoices()

    # Push all invoices and receipts to moneybird.
    _sync_food_orders()
    _sync_sales_orders()
    _sync_registrations()
    _sync_renewals()
    _sync_event_registrations()
    _sync_receipts()

    logger.info("Finished moneybird synchronization.")


def _delete_invoices():
    """Delete the invoices that have been marked for deletion from moneybird."""
    invoices = MoneybirdExternalInvoice.objects.filter(needs_deletion=True)
    logger.info("Deleting %d invoices.", invoices.count())

    moneybird = get_moneybird_api_service()
    for invoice in invoices:
        try:
            if invoice.moneybird_invoice_id is not None:
                moneybird.delete_external_sales_invoice(invoice.moneybird_invoice_id)
            invoice.delete()
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, invoice)


def _sync_outdated_invoices():
    """Resynchronize all invoices that have been marked as outdated."""
    invoices = MoneybirdExternalInvoice.objects.filter(
        needs_synchronization=True, needs_deletion=False
    ).order_by("payable_model", "object_id")

    logger.info("Resynchronizing %d invoices.", invoices.count())
    for invoice in invoices:
        try:
            instance = invoice.payable_object
        except ObjectDoesNotExist:
            logger.exception("Payable object for outdated invoice does not exist.")
        if instance is None:
            logger.exception("Payable object for outdated invoice does not exist.")

        try:
            create_or_update_external_invoice(instance)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, instance)


def _sync_contacts():
    logger.info("Synchronizing contacts...")
    # Make moneybird contacts for people that dont have.
    for member in Member.objects.filter(
        moneybird_contact__isnull=True, profile__is_minimized=False
    ):
        try:
            create_or_update_contact(member)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, member)

    # Update moneybird contacts that need synchronization.
    for contact in MoneybirdContact.objects.filter(needs_synchronization=True):
        try:
            create_or_update_contact(contact.member)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, contact.member)

    # Archive moneybrid contacts where mb contact has not been archived but user was minimized.
    for contact in MoneybirdContact.objects.filter(member__profile__is_minimized=True):
        try:
            delete_contact(contact)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, contact)

    _sync_contacts_with_outdated_mandates()


def _sync_contacts_with_outdated_mandates():
    """Update contacts with outdated mandates.

    This is mainly a workaround that allows creating contacts on moneybird for members
    that have a mandate valid from today, without pushing that mandate to Moneybird,
    as Moneybird only allows mandates valid from the past (and not from today).

    These contacts can be updated the next day using this function, wich syncs every
    contact where Moneybird doesn't have the correct mandate yet.
    """
    contacts = (
        MoneybirdContact.objects.annotate(
            sepa_mandate_id=Subquery(
                BankAccount.objects.filter(owner=OuterRef("member"))
                .order_by("-created_at")
                .values("mandate_no")[:1]
            )
        )
        .exclude(moneybird_sepa_mandate_id=F("sepa_mandate_id"))
        # For some reason the DB does not consider None == None in the exclude above.
        .exclude(sepa_mandate_id=None, moneybird_sepa_mandate_id=None)
    )

    logger.info(
        "Pushing %d contacts with outdated mandates to Moneybird.", contacts.count()
    )

    for contact in contacts:
        try:
            create_or_update_contact(contact.member)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, contact.member)


def _try_create_or_update_external_invoices(queryset):
    logger.info(
        "Pushing %d %s to Moneybird.", queryset.count(), model_ngettext(queryset)
    )

    for instance in queryset:
        try:
            create_or_update_external_invoice(instance)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, instance)


def _sync_food_orders():
    """Create invoices for new food orders."""
    logger.info("Synchronizing food orders...")
    food_orders = FoodOrder.objects.filter(
        food_event__event__start__date__gte=settings.MONEYBIRD_START_DATE,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=Cast(OuterRef("pk"), output_field=CharField()),
                payable_model=ContentType.objects.get_for_model(FoodOrder),
            )
        ),
    )

    _try_create_or_update_external_invoices(food_orders)


def _sync_sales_orders():
    """Create invoices for new sales orders."""
    logger.info("Synchronizing sales orders...")
    sales_orders = Order.objects.filter(
        shift__start__date__gte=settings.MONEYBIRD_START_DATE,
        payment__isnull=False,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=Cast(OuterRef("pk"), output_field=CharField()),
                payable_model=ContentType.objects.get_for_model(Order),
            )
        )
    )

    _try_create_or_update_external_invoices(sales_orders)


def _sync_registrations():
    """Create invoices for new, paid registrations."""
    logger.info("Synchronizing registrations...")
    registrations = Registration.objects.filter(
        created_at__date__gte=settings.MONEYBIRD_START_DATE,
        payment__isnull=False,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=Cast(OuterRef("pk"), output_field=CharField()),
                payable_model=ContentType.objects.get_for_model(Registration),
            )
        )
    )

    _try_create_or_update_external_invoices(registrations)


def _sync_renewals():
    """Create invoices for new, paid renewals."""
    logger.info("Synchronizing renewals...")
    renewals = Renewal.objects.filter(
        created_at__date__gte=settings.MONEYBIRD_START_DATE,
        payment__isnull=False,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=Cast(OuterRef("pk"), output_field=CharField()),
                payable_model=ContentType.objects.get_for_model(Renewal),
            )
        )
    )

    _try_create_or_update_external_invoices(renewals)


def _sync_event_registrations():
    """Create invoices for new event registrations, and delete invoices that shouldn't exist.

    Existing invoices are deleted when the event registration is cancelled, not invited, or free.
    In most cases, this will be done already because the event registration has been saved.
    However, some changes to the event or registrations for  the same event might not trigger saving
    the event registration, but still change its queue position or payment amount.
    """
    logger.info("Synchronizing event registrations...")
    event_registrations = (
        EventRegistration.objects.select_properties("queue_position", "payment_amount")
        .filter(
            event__start__date__gte=settings.MONEYBIRD_START_DATE,
            date_cancelled__isnull=True,
            queue_position__isnull=True,
            payment_amount__gt=0,
        )
        .exclude(
            Exists(
                MoneybirdExternalInvoice.objects.filter(
                    object_id=Cast(OuterRef("pk"), output_field=CharField()),
                    payable_model=ContentType.objects.get_for_model(EventRegistration),
                )
            )
        )
    )

    _try_create_or_update_external_invoices(event_registrations)

    to_remove = (
        EventRegistration.objects.select_properties("queue_position", "payment_amount")
        .filter(
            Q(date_cancelled__isnull=False)
            | Q(queue_position__isnull=False)
            | ~Q(payment_amount__gt=0),
            event__start__date__gte=settings.MONEYBIRD_START_DATE,
        )
        .filter(
            Exists(
                MoneybirdExternalInvoice.objects.filter(
                    object_id=Cast(OuterRef("pk"), output_field=CharField()),
                    payable_model=ContentType.objects.get_for_model(EventRegistration),
                )
            )
        )
    )

    logger.info(
        "Removing invoices for %d event registrations from Moneybird.",
        to_remove.count(),
    )

    for instance in to_remove:
        try:
            delete_external_invoice(instance)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, instance)


def _sync_receipts():
    # Reimbursements whose MoneybirdReceipt does not exist or has not been fully pushed yet.
    reimbursements = Reimbursement.objects.filter(
        verdict=Reimbursement.Verdict.APPROVED,
    ).exclude(
        moneybird_receipt__isnull=False,
        moneybird_receipt__moneybird_receipt_id__isnull=False,
        moneybird_receipt__moneybird_attachment_is_uploaded=False,
    )

    logger.info(
        "Pushing %d reimbursement receipts to Moneybird.", reimbursements.count()
    )

    for reimbursement in reimbursements:
        try:
            create_receipt(reimbursement)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, reimbursement)


def _sync_moneybird_payments():
    """Create financial statements with all payments that haven't been synced yet.

    This creates one statement per payment type for which there are new payments.
    """
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    logger.info("Synchronizing payments...")

    for payment_type in [Payment.CASH, Payment.CARD, Payment.TPAY]:
        payments = Payment.objects.filter(
            type=payment_type,
            moneybird_payment__isnull=True,
            created_at__date__gte=settings.MONEYBIRD_START_DATE,
        ).order_by("pk")

        if payments.count() == 0:
            continue

        logger.info(
            "Pushing %d %s payments to Moneybird.",
            payments.count(),
            payment_type,
        )

        financial_account_id = financial_account_id_for_payment_type(payment_type)
        reference = f"{payment_type} payments at {timezone.now():'%Y-%m-%d %H:%M'}"

        try:
            _create_payments_statement(payments, reference, financial_account_id)
        except Administration.Error as e:
            logger.exception("Moneybird synchronization error: %s", e)
            send_sync_error(e, reference)


def _create_payments_statement(payments, reference, financial_account_id):
    moneybird = get_moneybird_api_service()
    moneybird_payments = [MoneybirdPayment(payment=payment) for payment in payments]
    statement = {
        "financial_statement": {
            "financial_account_id": financial_account_id,
            "reference": reference,
            "financial_mutations_attributes": {
                str(i): payment.to_moneybird()
                for i, payment in enumerate(moneybird_payments)
            },
        }
    }

    response = moneybird.create_financial_statement(statement)

    # Store the returned mutation ids that we need to later link the mutations.s
    for i, moneybird_payment in enumerate(moneybird_payments):
        moneybird_payment.moneybird_financial_statement_id = response["id"]
        moneybird_payment.moneybird_financial_mutation_id = response[
            "financial_mutations"
        ][i]["id"]

    MoneybirdPayment.objects.bulk_create(moneybird_payments)


def delete_moneybird_payment(moneybird_payment):
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    index_nr = MoneybirdPayment.objects.filter(
        moneybird_financial_statement_id=moneybird_payment.moneybird_financial_statement_id
    ).count()  # Note that this is done post_save, so the payment itself isn't in the database anymore

    moneybird = get_moneybird_api_service()

    if index_nr == 0:
        # Delete the whole statement if it will become empty
        moneybird.delete_financial_statement(
            moneybird_payment.moneybird_financial_statement_id
        )
        return

    # If we're just removing a single payment from a statement, we first need to unlink it
    mutation_info = moneybird.get_financial_mutation_info(
        moneybird_payment.moneybird_financial_mutation_id
    )
    for linked_payment in mutation_info["payments"]:
        moneybird.unlink_mutation_from_booking(
            mutation_id=int(moneybird_payment.moneybird_financial_mutation_id),
            booking_id=int(linked_payment["id"]),
            booking_type="Payment",
        )

    # and then remove it from the statement
    moneybird.update_financial_statement(
        moneybird_payment.moneybird_financial_statement_id,
        {
            "financial_statement": {
                "financial_mutations_attributes": {
                    str(0): {
                        "id": moneybird_payment.moneybird_financial_mutation_id,
                        "_destroy": True,
                    }
                }
            }
        },
    )


def process_thalia_pay_batch(batch):
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    moneybird = get_moneybird_api_service()
    moneybird.create_financial_statement(
        {
            "financial_statement": {
                "financial_account_id": settings.MONEYBIRD_TPAY_FINANCIAL_ACCOUNT_ID,
                "reference": f"Settlement of Thalia Pay batch {batch.id}: {batch.description}",
                "financial_mutations_attributes": {
                    "0": {
                        "date": batch.processing_date.strftime("%Y-%m-%d"),
                        "message": f"Settlement of Thalia Pay batch {batch.id}: {batch.description}",
                        "amount": str(-1 * batch.total_amount()),
                    }
                },
            }
        }
    )
