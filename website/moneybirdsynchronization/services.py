import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, F, OuterRef, Subquery
from django.utils import timezone

from events.models import EventRegistration
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.emails import send_sync_error
from moneybirdsynchronization.models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
    financial_account_id_for_payment_type,
)
from moneybirdsynchronization.moneybird import get_moneybird_api_service
from payments.models import BankAccount, Payment
from pizzas.models import FoodOrder
from registrations.models import Registration, Renewal
from sales.models.order import Order
from thaliawebsite import settings

logger = logging.getLogger(__name__)


def create_or_update_contact(member):
    """Push a Django user/member to Moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return None

    moneybird_contact, _ = MoneybirdContact.objects.get_or_create(member=member)

    moneybird = get_moneybird_api_service()

    if moneybird_contact.moneybird_id is None:
        # Push the contact to Moneybird.
        response = moneybird.create_contact(moneybird_contact.to_moneybird())
        moneybird_contact.moneybird_id = response["id"]
        moneybird_contact.moneybird_sepa_mandate_id = response["sepa_mandate_id"]
    else:
        # Update the contact data (right now we always do this, but we could use the version to check if it's needed)
        response = moneybird.update_contact(
            moneybird_contact.moneybird_id, moneybird_contact.to_moneybird()
        )

    moneybird_contact.save()
    return moneybird_contact


def synchronize_moneybird():
    """Perform all synchronization to moneybird."""
    logger.info("Starting moneybird synchronization.")

    # First make sure all moneybird contacts' SEPA mandates are up to date.
    sync_contacts_with_outdated_mandates()

    # Push all payments to moneybird. This needs to be done before the invoices,
    # as creating/updating invoices will link the payments to the invoices if they
    # already exist on moneybird.
    sync_moneybird_payments()

    # Push all invoices to moneybird.
    _sync_food_orders()
    _sync_sales_orders()
    _sync_registrations()
    _sync_renewals()
    _sync_event_registrations()


def sync_contacts_with_outdated_mandates():
    """Update contacts with outdated mandates.

    This is mainly a workaround that allows creating contacts on moneybird for members
    that have a mandate valid from today, without pushing that mandate to Moneybird,
    as Moneybird only allows mandates valid from the past (and not from today).

    These contacts can be updated the next day using this function, wich syncs every
    contact where Moneybird doesn't have the correct mandate yet.
    """
    mandates_to_push = MoneybirdContact.objects.annotate(
        sepa_mandate_id=Subquery(
            BankAccount.objects.filter(owner=OuterRef("member"))
            .order_by("-created_at")
            .values("mandate_no")[:1]
        )
    ).exclude(moneybird_sepa_mandate_id=F("sepa_mandate_id"))

    if mandates_to_push.exists():
        logger.info(
            "Pushing %d contacts with outdated mandates to Moneybird.",
            mandates_to_push.count(),
        )

    for mandates in mandates_to_push:
        create_or_update_contact(mandates)


def delete_contact(member):
    """Delete a Django user/member from Moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    try:
        moneybird_contact = MoneybirdContact.objects.get(member=member)
    except MoneybirdContact.DoesNotExist:
        return

    if moneybird_contact.moneybird_id is None:
        moneybird_contact.delete()
        return

    moneybird = get_moneybird_api_service()
    moneybird.delete_contact(moneybird_contact.moneybird_id)
    moneybird_contact.delete()


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
        external_invoice.save()

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
    moneybird.delete_external_invoice(external_invoice.moneybird_invoice_id)
    external_invoice.delete()


def _sync_food_orders():
    """Create invoices for new food orders."""
    food_orders = FoodOrder.objects.filter(
        food_event__event__start__date__gte=settings.MONEYBIRD_START_DATE,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=OuterRef("pk"),
                payable_model=ContentType.objects.get_for_model(FoodOrder),
            )
        ),
    )

    if food_orders.exists():
        logger.info("Pushing %d food orders to Moneybird.", food_orders.count())
        for instance in food_orders:
            try:
                create_or_update_external_invoice(instance)
            except Administration.Error as e:
                send_sync_error(e, instance)
                logging.exception("Moneybird synchronization error: %s", e)


def _sync_sales_orders():
    """Create invoices for new sales orders."""
    sales_orders = Order.objects.filter(
        shift__start__date__gte=settings.MONEYBIRD_START_DATE,
        payment__isnull=False,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=OuterRef("pk"),
                payable_model=ContentType.objects.get_for_model(Order),
            )
        )
    )

    if sales_orders.exists():
        logger.info("Pushing %d sales orders to Moneybird.", sales_orders.count())
        for instance in sales_orders:
            try:
                create_or_update_external_invoice(instance)
            except Administration.Error as e:
                send_sync_error(e, instance)
                logging.exception("Moneybird synchronization error: %s", e)


def _sync_registrations():
    """Create invoices for new, paid registrations."""
    registrations = Registration.objects.filter(
        created_at__date__gte=settings.MONEYBIRD_START_DATE,
        payment__isnull=False,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=OuterRef("pk"),
                payable_model=ContentType.objects.get_for_model(Registration),
            )
        )
    )

    if registrations.exists():
        logger.info("Pushing %d registrations to Moneybird.", registrations.count())
        for instance in registrations:
            try:
                create_or_update_external_invoice(instance)
            except Administration.Error as e:
                send_sync_error(e, instance)
                logging.exception("Moneybird synchronization error: %s", e)


def _sync_renewals():
    """Create invoices for new, paid renewals."""
    renewals = Renewal.objects.filter(
        created_at__date__gte=settings.MONEYBIRD_START_DATE,
        payment__isnull=False,
    ).exclude(
        Exists(
            MoneybirdExternalInvoice.objects.filter(
                object_id=OuterRef("pk"),
                payable_model=ContentType.objects.get_for_model(Renewal),
            )
        )
    )

    if renewals.exists():
        logger.info("Pushing %d renewals to Moneybird.", renewals.count())
        for instance in renewals:
            try:
                create_or_update_external_invoice(instance)
            except Administration.Error as e:
                send_sync_error(e, instance)
                logging.exception("Moneybird synchronization error: %s", e)


def _sync_event_registrations():
    """Create invoices for new event registrations."""
    event_registrations = (
        EventRegistration.objects.select_properties("queue_position", "payment_amount")
        .filter(
            event__start__date__gte=settings.MONEYBIRD_START_DATE,
            date_cancelled__isnull=True,
            queue_position__isnull=True,
            payment_amount__isnull=False,
        )
        .exclude(
            Exists(
                MoneybirdExternalInvoice.objects.filter(
                    object_id=OuterRef("pk"),
                    payable_model=ContentType.objects.get_for_model(EventRegistration),
                )
            )
        )
    )

    if event_registrations.exists():
        logger.info(
            "Pushing %d event registrations to Moneybird.", event_registrations.count()
        )

        for instance in event_registrations:
            try:
                create_or_update_external_invoice(instance)
            except Administration.Error as e:
                send_sync_error(e, instance)
                logging.exception("Moneybird synchronization error: %s", e)


def sync_moneybird_payments():
    """Create financial statements with all payments that haven't been synced yet.

    This creates one statement per payment type for which there are new payments.
    """
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    moneybird = get_moneybird_api_service()

    for payment_type in [Payment.TPAY, Payment.CARD, Payment.CASH]:
        payments = Payment.objects.filter(
            type=payment_type,
            moneybird_payment__isnull=True,
            created_at__date__gte=settings.MONEYBIRD_START_DATE,
        )

        if payments.count() == 0:
            continue

        logger.info(
            "Pushing %d %s payments to Moneybird.", payments.count(), payment_type
        )

        financial_account_id = financial_account_id_for_payment_type(payment_type)
        reference = f"{payment_type} payments at {timezone.now():'%Y-%m-%d %H:%M'}"

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

    if moneybird_payment.moneybird_financial_statement_id is None:
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
