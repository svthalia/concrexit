"""The signals checked by the moneybrid synchronization package."""
from django.db.models.signals import post_save, pre_delete
from django.template.defaultfilters import date

from utils.models.signals import suspendingreceiver

from members.models import Member
from moneybirdsynchronization.models import Contact
from moneybirdsynchronization.administration import HttpsAdministration
from thaliawebsite import settings
from django.contrib.auth.models import User

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
    if contact.moneybird_version is None:
        pass
    else:
        response = api.patch("contacts/{}".format(contact.moneybird_id), contact.to_moneybird())
        contact.moneybird_version = response["version"]
        contact.save()

@suspendingreceiver(
    post_save,
    sender="payments.Payment",
)
def post_payment_save(sender, instance, **kwargs):
    """Create external invoice on payment creation."""
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    contact = Contact.objects.get(member=instance.paid_by)

    dir(instance)

    projects = api.get("projects")
    project_id = None
    project_name = None

    if hasattr(instance, "order"):
        order = instance.order
        dir(order.shift)
        if hasattr(order.shift, "event"):
            event = order.shift.event
            start_date = date(event.start, "Y-m-d")
            project_name = f"{event.title} [{start_date}]"

    elif hasattr(instance, "event"):
        event = order.shift.event
        start_date = date(event.start, "Y-m-d")
        project_name = f"{event.title} [{start_date}]"
    
    if project_name is not None:
        for project in projects:
            if project["name"] == project_name:
                project_id = project["id"]
                break
        
        if project_id is None:
            project_id = api.post("projects", {"name": project_name})["id"]


    invoice_info = None
    if project_name is None:
        invoice_info = {
            "external_sales_invoice": 
            {
                "contact_id": contact.moneybird_id,
                "reference": str(instance.id),
                "date": instance.created_at.strftime("%Y-%m-%d"),
                "source_url": settings.BASE_URL + instance.get_admin_url(),
                "currency": "EUR",
                "prices_are_incl_tax": True,
                "details_attributes":[
                    {
                        "description": instance.topic,
                        "price": str(instance.amount),
                    },
                ],
            }
        }
    else:
        invoice_info = {
            "external_sales_invoice": 
            {
                "contact_id": contact.moneybird_id,
                "reference": str(instance.id),
                "date": instance.created_at.strftime("%Y-%m-%d"),
                "source_url": settings.BASE_URL + instance.get_admin_url(),
                "currency": "EUR",
                "prices_are_incl_tax": True,
                "details_attributes":[
                    {
                        "description": instance.topic,
                        "price": str(instance.amount),
                        "project_id": project_id,
                    },
                ],
            }
        }

    print(invoice_info)
    api.post("external_sales_invoices", invoice_info)