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
    contact = MoneybirdContact.objects.get(member=member)
    apiservice.api.delete(f"contacts/{contact.moneybird_id}")
    contact.delete()


def register_event_registration_payment(instance):
    if settings.MONEYBIRD_SYNC_ENABLED is False:
        return

    apiservice = get_moneybird_api_service()
    contact_id = apiservice.api.get(
        f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}"
    )["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = MoneybirdContact.objects.get(
                member=instance.member
            ).moneybird_id
        except MoneybirdContact.DoesNotExist:
            pass

    start_date = date(instance.event.start, "Y-m-d")
    project_name = f"{instance.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)

    invoice_info = {
        "external_sales_invoice": {
            "contact_id": contact_id,
            "reference": str(instance.payment.id),
            "date": instance.payment.created_at.strftime("%Y-%m-%d"),
            "source_url": settings.BASE_URL + instance.payment.get_admin_url(),
            "currency": "EUR",
            "prices_are_incl_tax": True,
            "details_attributes": [
                {
                    "description": instance.payment.topic,
                    "price": str(instance.payment.amount),
                    "project_id": project_id,
                },
            ],
        }
    }

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
        contact_id = apiservice.api.get(
            f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}"
        )["id"]
        if order.payer is not None:
            try:
                contact_id = MoneybirdContact.objects.get(
                    member=order.payer
                ).moneybird_id
            except MoneybirdContact.DoesNotExist:
                pass

        invoice_info = {
            "external_sales_invoice": {
                "contact_id": contact_id,
                "reference": str(order.payment.id),
                "date": order.payment.created_at.strftime("%Y-%m-%d"),
                "source_url": settings.BASE_URL + order.payment.get_admin_url(),
                "currency": "EUR",
                "prices_are_incl_tax": True,
                "details_attributes": [
                    {
                        "description": order.payment.topic,
                        "price": str(order.payment.amount),
                        "project_id": project_id,
                    },
                ],
            }
        }

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

    contact_id = apiservice.api.get(
        f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}"
    )["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = MoneybirdContact.objects.get(
                member=instance.member
            ).moneybird_id
        except MoneybirdContact.DoesNotExist:
            pass

    start_date = date(instance.food_event.event.start, "Y-m-d")
    project_name = f"{instance.food_event.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)

    invoice_info = {
        "external_sales_invoice": {
            "contact_id": contact_id,
            "reference": str(instance.payment.id),
            "date": instance.payment.created_at.strftime("%Y-%m-%d"),
            "source_url": settings.BASE_URL + instance.payment.get_admin_url(),
            "currency": "EUR",
            "prices_are_incl_tax": True,
            "details_attributes": [
                {
                    "description": instance.payment.topic,
                    "price": str(instance.payment.amount),
                    "project_id": project_id,
                },
            ],
        }
    }

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

    contact_id = apiservice.api.get(
        f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}"
    )["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = MoneybirdContact.objects.get(
                member=instance.payment.paid_by
            ).moneybird_id
        except MoneybirdContact.DoesNotExist:
            pass

    invoice_info = {
        "external_sales_invoice": {
            "contact_id": contact_id,
            "reference": str(instance.payment.id),
            "date": instance.payment.created_at.strftime("%Y-%m-%d"),
            "source_url": settings.BASE_URL + instance.payment.get_admin_url(),
            "currency": "EUR",
            "prices_are_incl_tax": True,
            "details_attributes": [
                {
                    "description": instance.payment.topic,
                    "price": str(instance.payment.amount),
                    "ledger_id": apiservice.api.get("ledger_accounts"),
                },
            ],
        }
    }

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

    apiservice.api.delete(f"external_sales_invoices/{instance.moneybird_invoice_id}")
    if instance.moneybird_financial_statement_id is not None:
        try:
            apiservice.api.patch(
                f"financial_statements/{instance.moneybird_financial_statement_id}",
                {
                    "financial_statement": {
                        "financial_mutations_attributes": {
                            "0": {
                                "id": instance.moneybird_financial_mutation_id,
                                "_destroy": True,
                            }
                        }
                    }
                },
            )
        except Administration.InvalidData:
            apiservice.api.delete(
                f"financial_statements/{instance.moneybird_financial_statement_id}"
            )


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
            response = apiservice.api.post("contacts", contact.to_moneybird())
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
            response = apiservice.api.delete(f"contacts/{moneybird['id']}")


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
