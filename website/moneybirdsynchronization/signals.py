"""The signals checked by the moneybrid synchronization package."""
from django.db.models.signals import post_save, pre_save, pre_delete
from django.template.defaultfilters import date
from django.core.exceptions import ObjectDoesNotExist

from utils.models.signals import suspendingreceiver

from members.models import Member
from moneybirdsynchronization.models import Contact
from moneybirdsynchronization.administration import HttpsAdministration
from moneybirdsynchronization import services
from events.models import EventRegistration
from sales.models.order import Order
from sales.models.shift import Shift
from payments.models import Payment
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
    sender="events.EventRegistration",
)
def post_event_registration_payment(sender, instance, update_fields, **kwargs):
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
    

# @suspendingreceiver(
#     post_save,
#     sender="payments.Payment",
# )
# def post_payment_save(sender, instance, **kwargs):
#     """Create external invoice on payment creation."""
#     api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
#     try:
#         contact = Contact.objects.get(member=instance.paid_by)
#     except Contact.DoesNotExist:
#         return

#     dir(instance)


#     projects = api.get("projects")
#     project_id = None
#     project_name = None

#     print(EventRegistration.objects.filter(payment=instance))

#     if hasattr(instance, "order"):
#         print("order")
#         order = instance.order
#         dir(order.shift)
#         if hasattr(order.shift, "event"):
#             event = order.shift.event
#             start_date = date(event.start, "Y-m-d")
#             project_name = f"{event.title} [{start_date}]"

#     elif hasattr(instance, "events_registration"):
#         print("event")
#         event = instance.event
#         start_date = date(event.start, "Y-m-d")
#         project_name = f"{event.title} [{start_date}]"
        
#     else:
#         print("else")
#         project_name = None
    
#     if project_name is not None:
#         print("project_name is not None")
#         for project in projects:
#             if project["name"] == project_name:
#                 project_id = project["id"]
#                 break
        
#         if project_id is None:
#             print("project_id is None")
#             project_id = api.post("projects", {"name": project_name})["id"]
#             print(project_id)
    
#     ThaliaPayId = services.get_financial_account_id(api, "ThaliaPay ThaliaPay")
#     print(ThaliaPayId)

#     invoice_info = None
#     if project_name is None:
#         invoice_info = {
#             "external_sales_invoice": 
#             {
#                 "contact_id": contact.moneybird_id,
#                 "reference": str(instance.id),
#                 "date": instance.created_at.strftime("%Y-%m-%d"),
#                 "source_url": settings.BASE_URL + instance.get_admin_url(),
#                 "currency": "EUR",
#                 "prices_are_incl_tax": True,
#                 "details_attributes":[
#                     {
#                         "description": instance.topic,
#                         "price": str(instance.amount),
#                     },
#                 ],
#             }
#         }
#     else:
#         invoice_info = {
#             "external_sales_invoice": 
#             {
#                 "contact_id": contact.moneybird_id,
#                 "reference": str(instance.id),
#                 "date": instance.created_at.strftime("%Y-%m-%d"),
#                 "source_url": settings.BASE_URL + instance.get_admin_url(),
#                 "currency": "EUR",
#                 "prices_are_incl_tax": True,
#                 "details_attributes":[
#                     {
#                         "description": instance.topic,
#                         "price": str(instance.amount),
#                         "project_id": project_id,
#                     },
#                 ],
#             }
#         }

#     api.post("external_sales_invoices", invoice_info)