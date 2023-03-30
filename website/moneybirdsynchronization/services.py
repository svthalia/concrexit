import datetime

from django.db.models import OuterRef, Q, Subquery
from django.template.defaultfilters import date

from moneybirdsynchronization import emails
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.models import MoneybirdContact, MoneybirdExternalInvoice
from moneybirdsynchronization.moneybird import MoneybirdAPIService

from events.models.event import Event
from members.models import Member
from payments.models import Payment
from thaliawebsite import settings


def get_moneybird_api_service():
    if (
        settings.MONEYBIRD_ADMINISTRATION_ID is None
        or settings.MONEYBIRD_API_KEY is None
    ):
        raise RuntimeError("Moneybird API key or administration ID not set")
    return MoneybirdAPIService(
        settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID
    )


def push_thaliapay_batch(batch):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    payments = Payment.objects.filter(batch=batch)
    tpay_account_id = settings.MONEYBIRD_THALIAPAY_FINANCIAL_ACCOUNT_ID
    apiservice.link_transaction_to_financial_account(tpay_account_id, payments)


def update_contact(member):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    apiservice.update_contact(MoneybirdContact.objects.get_or_create(member=member)[0])


def delete_contact(member):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    apiservice.delete_contact(MoneybirdContact.objects.get(member=member))


def create_external_invoice(payment):
    external_invoice = MoneybirdExternalInvoice(payment=payment)
    external_invoice.save()


def register_event_registration_payment(registration):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    contact_id = apiservice.get_contact_id_by_customer(registration)

    start_date = date(registration.event.start, "Y-m-d")
    project_name = f"{registration.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)

    invoice_info = apiservice.create_external_sales_info(
        contact_id, registration.payment, project_id
    )

    try:
        response = apiservice.create_external_sales_invoice(invoice_info)
        registration.payment.moneybird_external_invoice.moneybird_invoice_id = response[
            "id"
        ]
        registration.payment.moneybird_external_invoice.save()
    except Administration.Error as e:
        emails.send_sync_error(e, registration.payment.moneybird_external_invoice)


def register_shift_payments(orders, instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    try:
        event = Event.objects.get(shifts=instance)
        start_date = date(event.start, "Y-m-d")
        project_name = f"{event.title} [{start_date}]"
    except Event.DoesNotExist:
        start_date = date(instance.start, "Y-m-d")
        project_name = f"{instance} [{start_date}]"

    project_id = apiservice.get_project_id(project_name)

    for order in orders:
        contact_id = apiservice.get_contact_id_by_customer(order)

        invoice_info = apiservice.create_external_sales_info(
            contact_id, order.payment, project_id
        )

        try:
            response = apiservice.create_external_sales_invoice(invoice_info)
            order.payment.moneybird_external_invoice.moneybird_invoice_id = response[
                "id"
            ]
            order.payment.moneybird_external_invoice.save()
        except Administration.Error as e:
            emails.send_sync_error(e, order.payment.moneybird_external_invoice)


def register_food_order_payment(food_order):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    contact_id = apiservice.get_contact_id_by_customer(food_order)

    start_date = date(food_order.food_event.event.start, "Y-m-d")
    project_name = f"{food_order.food_event.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)

    invoice_info = apiservice.create_external_sales_info(
        contact_id, food_order.payment, project_id
    )

    try:
        response = apiservice.create_external_sales_invoice(invoice_info)
        food_order.payment.moneybird_external_invoice.moneybird_invoice_id = response[
            "id"
        ]
        food_order.payment.moneybird_external_invoice.save()
    except Administration.Error as e:
        emails.send_sync_error(e, food_order.payment.moneybird_external_invoice)


def register_contribution_payment(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    contact_id = apiservice.get_contact_id_by_customer(instance)

    invoice_info = apiservice.create_external_sales_info(
        contact_id, instance.payment, contribution=True
    )

    try:
        response = apiservice.create_external_sales_invoice(invoice_info)
        instance.payment.moneybird_external_invoice.moneybird_invoice_id = response[
            "id"
        ]
        instance.payment.moneybird_external_invoice.save()
    except Administration.Error as e:
        emails.send_sync_error(e, instance.payment.moneybird_external_invoice)


def delete_payment(payment):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    apiservice.delete_external_invoice(payment.moneybird_external_invoice)


def sync_contacts():
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    members_without_contact = Member.objects.filter(
        ~Q(
            id__in=Subquery(
                MoneybirdContact.objects.filter(member=OuterRef("pk")).values("member")
            )
        )
    )

    for member in members_without_contact:
        contact = MoneybirdContact(member=member)
        contact.save()

    # fetch contact ids from moneybird
    api_response = apiservice.api.get("contacts")

    # fetch contact ids from contact model
    contact_info = [
        contact.get_moneybird_info() for contact in MoneybirdContact.objects.all()
    ]

    # find contacts in contact model that are not in moneybird and add to moneybird
    moneybird_ids = [int(info["id"]) for info in api_response]
    for contact in contact_info:
        if contact["id"] is None or int(contact["id"]) not in moneybird_ids:
            contact = MoneybirdContact.objects.get(
                member=Member.objects.get(pk=contact["pk"])
            )
            response = apiservice.add_contact(contact)
            contact.moneybird_id = response["id"]
            contact.moneybird_version = response["version"]
            contact.save()

    moneybird_info = []
    for contact in api_response:
        if len(contact["custom_fields"]) > 0:
            moneybird_info.append(
                {
                    "id": contact["id"],
                    "version": contact["version"],
                    "pk": contact["custom_fields"][0]["value"],
                }
            )

    ids = [info["id"] for info in contact_info]
    for moneybird in moneybird_info:
        if int(moneybird["id"]) not in ids:
            apiservice.delete_contact(moneybird["id"])


def sync_statements():
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    date = datetime.date.today()
    new_card_payments = Payment.objects.filter(
        type=Payment.CARD,
        created_at__year=date.year,
        created_at__month=date.month,
        created_at__day=date.day,
        moneybird_external_invoice__moneybird_financial_statement_id=None,
    )
    new_cash_payments = Payment.objects.filter(
        type=Payment.CASH,
        created_at__year=date.year,
        created_at__month=date.month,
        created_at__day=date.day,
        moneybird_external_invoice__moneybird_financial_statement_id=None,
    )

    apiservice.link_transaction_to_financial_account(
        settings.MONEYBIRD_PIN_FINANCIAL_ACCOUNT_ID, new_card_payments
    )
    apiservice.link_transaction_to_financial_account(
        settings.MONEYBIRD_CASHTANJE_FINANCIAL_ACCOUNT_ID, new_cash_payments
    )
