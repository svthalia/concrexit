import datetime

from django.db.models import OuterRef, Q, Subquery
from django.template.defaultfilters import date

from moneybirdsynchronization import emails
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.models import MoneybirdContact
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
        return RuntimeError("Moneybird API key or administration ID not set")
    return MoneybirdAPIService(
        settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID
    )


def push_thaliapay_batch(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    payments = Payment.objects.filter(batch=instance)
    tpay_account_id = apiservice.get_financial_account_id("ThaliaPay")
    apiservice.link_transaction_to_financial_account(tpay_account_id, payments)


def update_contact(member):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    apiservice.update_contact(MoneybirdContact.objects.get_or_create(member=member)[0])


def delete_contact(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    member = Member.objects.get(profile=instance)
    apiservice.delete_contact(MoneybirdContact.objects.get(member=member))


def register_event_registration_payment(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    contact_id = apiservice.get_contact_id_by_customer(instance)

    start_date = date(instance.event.start, "Y-m-d")
    project_name = f"{instance.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)

    invoice_info = apiservice.create_external_sales_info(
        contact_id, instance, project_id
    )

    try:
        response = apiservice.api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Administration.Error as e:
        emails.send_sync_error(e, instance.payment)


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
        contact_id = apiservice.get_contact_id_by_customer(instance)

        invoice_info = apiservice.create_external_sales_info(
            contact_id, order, project_id
        )

        try:
            response = apiservice.api.post("external_sales_invoices", invoice_info)
            order.payment.moneybird_invoice_id = response["id"]
            order.payment.save()
        except Administration.Error as e:
            emails.send_sync_error(e, instance.payment)


def register_food_order_payment(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    contact_id = apiservice.get_contact_id_by_customer(instance)

    start_date = date(instance.food_event.event.start, "Y-m-d")
    project_name = f"{instance.food_event.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)

    invoice_info = apiservice.create_external_sales_info(
        contact_id, instance, project_id
    )

    try:
        response = apiservice.api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Administration.Error as e:
        emails.send_sync_error(e, instance.payment)


def register_contribution_payment(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()

    contact_id = apiservice.get_contact_id_by_customer(instance)

    invoice_info = apiservice.create_external_sales_info(
        contact_id, instance, contribution=True
    )

    try:
        response = apiservice.api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Administration.Error as e:
        emails.send_sync_error(e, instance.payment)


def delete_payment(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    apiservice.delete_external_invoice(instance)


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
            response = apiservice.add_contact_to_moneybird(contact)
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
        moneybird_financial_statement_id=None,
    )
    new_cash_payments = Payment.objects.filter(
        type=Payment.CASH,
        created_at__year=date.year,
        created_at__month=date.month,
        created_at__day=date.day,
        moneybird_financial_statement_id=None,
    )

    card_account_id = apiservice.get_financial_account_id(
        settings.PAYMENT_TYPE_TO_FINANCIAL_ACCOUNT_MAPPING["card"]
    )
    apiservice.link_transaction_to_financial_account(card_account_id, new_card_payments)

    cash_account_id = apiservice.get_financial_account_id(
        settings.PAYMENT_TYPE_TO_FINANCIAL_ACCOUNT_MAPPING["cash"]
    )
    apiservice.link_transaction_to_financial_account(cash_account_id, new_cash_payments)
