from moneybirdsynchronization.models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
    financial_account_id_for_payment_type,
)
from moneybirdsynchronization.moneybird import get_moneybird_api_service

from thaliawebsite import settings


def create_or_update_contact(member):
    """Push a Django user/member to Moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return None

    moneybird_contact, _ = MoneybirdContact.objects.get_or_create(member=member)

    moneybird = get_moneybird_api_service()

    if moneybird_contact.moneybird_id is None:
        # Push the contact to Moneybird
        response = moneybird.create_contact(moneybird_contact.to_moneybird())
        moneybird_contact.moneybird_id = response["id"]
        moneybird_contact.moneybird_version = response["version"]
        moneybird_contact.save()
    else:
        # Update the contact data
        # TODO (not really important) only update the fields that have changed (which you can check with the version)
        response = moneybird.update_contact(
            moneybird_contact.moneybird_id, moneybird_contact.to_moneybird()
        )
        moneybird_contact.moneybird_version = response["version"]
        moneybird_contact.save()

    return moneybird_contact


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
        if (
            external_invoice.payable.payment.moneybird_payment.moneybird_financial_mutation_id
            is not None
        ):
            # If the payment itself also already exists in a financial mutation, link it
            moneybird.link_mutation_to_booking(
                mutation_id=external_invoice.payable.payment.moneybird_payment.moneybird_financial_mutation_id,
                booking_id=external_invoice.moneybird_invoice_id,
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


def _create_statement_and_add_payment(moneybird_payment, financial_account_id):
    """Create a new financial statement and attach this moneybird payment to it."""
    moneybird = get_moneybird_api_service()

    reference = f"{moneybird_payment.payment.type} payments for {moneybird_payment.payment.created_at:'%Y-%m-%d'}"

    response = moneybird.create_financial_statement(
        {
            "financial_statement": {
                "financial_account_id": financial_account_id,
                "reference": reference,
                "financial_mutations_attributes": {
                    "0": moneybird_payment.to_moneybird()
                },
            }
        }
    )
    moneybird_payment.moneybird_financial_statement_id = response["id"]
    moneybird_payment.moneybird_financial_mutation_id = response["financial_mutations"][
        0
    ]["id"]
    moneybird_payment.save()
    return moneybird_payment


def _add_payment_to_statement(moneybird_payment, financial_statement_id):
    """Add the moneybird payment to the financial statement."""
    moneybird = get_moneybird_api_service()

    index_nr = MoneybirdPayment.objects.filter(
        moneybird_financial_statement_id=financial_statement_id
    ).count()

    response = moneybird.update_financial_statement(
        financial_statement_id,
        {
            "financial_statement": {
                "financial_mutations_attributes": {
                    str(index_nr): moneybird_payment.to_moneybird()
                }
            }
        },
    )
    moneybird_payment.moneybird_financial_statement_id = financial_statement_id
    moneybird_payment.moneybird_financial_mutation_id = response["financial_mutations"][
        index_nr
    ]["id"]
    moneybird_payment.save()
    return moneybird_payment


def create_moneybird_payment(payment):
    """Create a payment on Moneybird."""
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return None

    financial_account_id = financial_account_id_for_payment_type(payment.type)
    if financial_account_id is None:
        # Don't sync if there's no financial account connected
        # for example, 'other' payments (like wire transfers), don't have concrexit as source for financial
        # mutation statements. So we ignore those and leave it to Moneybird itself.
        return None

    moneybird_payment, _ = MoneybirdPayment.objects.get_or_create(payment=payment)

    if moneybird_payment.moneybird_financial_mutation_id is None:
        last_payment_in_same_statement = MoneybirdPayment.objects.filter(
            payment__type=payment.type,
            payment__created_at__date=payment.created_at.date(),
            moneybird_financial_statement_id__isnull=False,
        ).first()

        if last_payment_in_same_statement is not None:
            # There already exists a statement we can add this payment to
            existing_statement_id = (
                last_payment_in_same_statement.moneybird_financial_statement_id
            )
            _add_payment_to_statement(moneybird_payment, existing_statement_id)
        else:
            _create_statement_and_add_payment(moneybird_payment, financial_account_id)

    # Note we don't need an else-branch because payments are immutable, so there's no need to update a payment ever

    return moneybird_payment


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
    for linked_payment in mutation_info[0]["payments"]:
        moneybird.unlink_mutation_from_booking(
            mutation_id=moneybird_payment.moneybird_financial_mutation_id,
            booking_id=linked_payment["id"],
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


#
#
# def push_thaliapay_batch(batch):
#     if not settings.MONEYBIRD_SYNC_ENABLED:
#         return
#
#     payments = Payment.objects.filter(batch=batch)
#     tpay_account_id = settings.MONEYBIRD_THALIAPAY_FINANCIAL_ACCOUNT_ID
#
#     apiservice = get_moneybird_api_service()
#     apiservice.link_transaction_to_financial_account(tpay_account_id, payments)
#     batch.pushed_thaliapay_batch.processed = True
#     batch.pushed_thaliapay_batch.save()
#
# def sync_contacts():
#     if not settings.MONEYBIRD_SYNC_ENABLED:
#         return
#
#     apiservice = get_moneybird_api_service()
#
#     unsynced_members = Member.objects.filter(
#         ~Q(
#             id__in=Subquery(
#                 MoneybirdContact.objects.filter(member=OuterRef("pk")).values("member")
#             )
#         )
#     )
#
#     for member in unsynced_members:
#         contact = MoneybirdContact(member=member)
#         contact.save()
#
#     # fetch contact ids from moneybird
#     api_response = apiservice.api.get("contacts")
#
#     # fetch contact ids from contact model
#     contact_info = [
#         contact.get_moneybird_info() for contact in MoneybirdContact.objects.all()
#     ]
#
#     # find contacts in contact model that are not in moneybird and add to moneybird
#     moneybird_ids = [int(info["id"]) for info in api_response]
#     for contact in contact_info:
#         if contact["id"] is None or int(contact["id"]) not in moneybird_ids:
#             contact = MoneybirdContact.objects.get(
#                 member=Member.objects.get(pk=contact["pk"])
#             )
#             response = apiservice.create_contact(contact)
#             contact.moneybird_id = response["id"]
#             contact.moneybird_version = response["version"]
#             contact.save()
#
#     moneybird_info = []
#     for contact in api_response:
#         if len(contact["custom_fields"]) > 0:
#             moneybird_info.append(
#                 {
#                     "id": contact["id"],
#                     "version": contact["version"],
#                     "pk": contact["custom_fields"][0]["value"],
#                 }
#             )
#
#     ids = [info["id"] for info in contact_info]
#     for moneybird in moneybird_info:
#         if int(moneybird["id"]) not in ids:
#             apiservice.delete_contact(moneybird["id"])
#
#
# def sync_statements():
#     if not settings.MONEYBIRD_SYNC_ENABLED:
#         return
#
#     apiservice = get_moneybird_api_service()
#
#     date = datetime.date.today()
#     new_card_payments = Payment.objects.filter(
#         type=Payment.CARD,
#         created_at__year=date.year,
#         created_at__month=date.month,
#         created_at__day=date.day,
#         moneybird_external_invoice__moneybird_financial_statement_id=None,
#     )
#     new_cash_payments = Payment.objects.filter(
#         type=Payment.CASH,
#         created_at__year=date.year,
#         created_at__month=date.month,
#         created_at__day=date.day,
#         moneybird_external_invoice__moneybird_financial_statement_id=None,
#     )
#
#     apiservice.link_transaction_to_financial_account(
#         settings.MONEYBIRD_PIN_FINANCIAL_ACCOUNT_ID, new_card_payments
#     )
#     apiservice.link_transaction_to_financial_account(
#         settings.MONEYBIRD_CASH_FINANCIAL_ACCOUNT_ID, new_cash_payments
#     )
