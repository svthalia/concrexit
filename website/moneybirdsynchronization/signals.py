"""The signals checked by the moneybrid synchronization package."""
from django.db.models.signals import post_save, pre_delete
from django.template.defaultfilters import date
import logging

from utils.models.signals import suspendingreceiver

from members.models import Member
from moneybirdsynchronization.models import Contact
from moneybirdsynchronization.administration import HttpsAdministration
from payments.models import Payment
from thaliawebsite import settings

@suspendingreceiver(
    post_save,
    sender="members.Profile",
)
def post_profile_save(sender, instance, **kwargs):
    """Update contact on profile creation."""
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    member = Member.objects.get(profile=instance)
    contact = Contact.objects.get_or_create(member=member)[0]
    if contact.moneybird_version is None:
        response = api.post("contacts", contact.to_moneybird())
        contact.moneybird_id = response["id"]
        contact.moneybird_version = response["version"]
        contact.save()
    else:
        response = api.patch("contacts/{}".format(contact.moneybird_id), contact.to_moneybird())
        contact.moneybird_version = response["version"]
        contact.save()


@suspendingreceiver(
    pre_delete,
    sender="members.Profile",
)
def post_profile_delete(sender, instance, **kwargs):
    """Delete contact on profile deletion."""
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    member = Member.objects.get(profile=instance)
    contact = Contact.objects.get(member=member)
    api.delete("contacts/{}".format(contact.moneybird_id))
    contact.delete()


@suspendingreceiver(
    post_save,
    sender="auth.User",
)
def post_user_save(sender, instance, **kwargs):
    """Update contact on user creation."""
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    contact = Contact.objects.get_or_create(member=instance)[0]
    if contact.moneybird_version is not None:
        response = api.patch("contacts/{}".format(contact.moneybird_id), contact.to_moneybird())
        contact.moneybird_version = response["version"]
        contact.save()


@suspendingreceiver(
    post_save,
    sender="events.EventRegistration",
)
def post_event_registration_payment(sender, instance, **kwargs):
    """ Create external invoice on payment creation."""
    if instance.payment is None:
        return
    if instance.payment.moneybird_invoice_id is not None:
        return
    
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    contact_id = api.get("contacts/customer_id/34")["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = Contact.objects.get(member=instance.payment.paid_by).moneybird_id
        except:
            pass


    start_date = date(instance.event.start, "Y-m-d")
    project_name = f"{instance.event.title} [{start_date}]"
    project_id = None
    
    for project in api.get("projects"):
        if project["name"] == project_name:
            project_id = project["id"]
            break
        
    if project_id is None:
        project_id = api.post("projects", {"project": {"name": project_name}})["id"]
    
    invoice_info = {
        "external_sales_invoice": 
        {
            "contact_id": contact_id,
            "reference": str(instance.payment.id),
            "date": instance.payment.created_at.strftime("%Y-%m-%d"),
            "source_url": settings.BASE_URL + instance.payment.get_admin_url(),
            "currency": "EUR",
            "prices_are_incl_tax": True,
            "details_attributes":[
                {
                    "description": instance.payment.topic,
                    "price": str(instance.payment.amount),
                    "project_id": project_id,
                },
            ],
        }
    }

    try:
        response = api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Exception as e:
        pass

    payment_identifiers = {
        Payment.TPAY: "ThaliaPay",
        Payment.CASH: "cashtanje",
        Payment.CARD: "pin"
    }

    if instance.payment.type != Payment.WIRE:
        account_id = None
        for account in api.get("financial_accounts"):
            if account["identifier"] == payment_identifiers[instance.payment.type]:
                account_id = account["id"]
                break
        if account_id is not None:
            payment_response = api.post("external_sales_invoices/{}/payments".format(response["id"]), 
                {"payment": {
                    "payment_date": instance.payment.created_at.strftime("%Y-%m-%d"),
                    "price": str(instance.payment.amount),
                    "financial_account_id": account_id, 
                    "manual_payment_action": "payment_without_proof",
                    "invoice_id": response["id"],
                    }
                }
            )

            statement_response = api.post("financial_statements",
                {"financial_statement": {
                    "financial_account_id": account_id,
                    "reference": str(instance.payment.id),
                    "financial_mutations_attributes": [
                        {
                            "date": instance.payment.created_at.strftime("%Y-%m-%d"),
                            "amount": str(instance.payment.amount),
                            "message": instance.payment.topic,
                        }
                    ]}
                }
            )

            mutation_response = api.patch("financial_mutations/{}/link_booking".format(statement_response["financial_mutations"][0]["id"]),{
                "booking_type": "ExternalSalesInvoice",
                "booking_id": response["id"],
                "price": str(instance.payment.amount),
                "description": instance.payment.topic,
                "project_id": project_id,
            })