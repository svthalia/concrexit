"""The signals checked by the moneybrid synchronization package."""
from django.db.models.signals import pre_save, post_save, pre_delete
from django.template.defaultfilters import date
import logging

from utils.models.signals import suspendingreceiver

from members.models import Member
from moneybirdsynchronization.models import Contact
from moneybirdsynchronization.administration import HttpsAdministration, Administration
from moneybirdsynchronization import services
from payments.models import Payment
from sales.models.order import Order
from events.models.event import Event
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
            contact_id = Contact.objects.get(member=instance.member).moneybird_id
        except:
            pass


    start_date = date(instance.event.start, "Y-m-d")
    project_name = f"{instance.event.title} [{start_date}]"
    project_id = services.get_project_id(api, project_name)
    
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


@suspendingreceiver(
    post_save,
    sender="sales.Shift",
)
def post_shift_save(sender, instance, **kwargs):
    if not instance.locked:
        return
    
    orders = Order.objects.filter(shift=instance)
    if len(orders) == 0:
        return
    if orders[0].payment.moneybird_invoice_id is not None:
        return
    try: 
        event = Event.objects.get(shifts=instance)
        start_date = date(event.start, "Y-m-d")
        project_name = f"{event.title} [{start_date}]"
    except:
        start_date = date(instance.start, "Y-m-d")
        project_name = f"{instance.__str__()} [{start_date}]"
    
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    project_id = services.get_project_id(api, project_name)

    for order in orders:
        contact_id = api.get("contacts/customer_id/34")["id"]
        if order.payer is not None:
            try:
                contact_id = Contact.objects.get(member=order.payer).moneybird_id
            except:
                pass

        invoice_info = {
            "external_sales_invoice": 
            {
                "contact_id": contact_id,
                "reference": str(order.payment.id),
                "date": order.payment.created_at.strftime("%Y-%m-%d"),
                "source_url": settings.BASE_URL + order.payment.get_admin_url(),
                "currency": "EUR",
                "prices_are_incl_tax": True,
                "details_attributes":[
                    {
                        "description": order.payment.topic,
                        "price": str(order.payment.amount),
                        "project_id": project_id,
                    },
                ],
            }
        }

        try:
            response = api.post("external_sales_invoices", invoice_info)
            order.payment.moneybird_invoice_id = response["id"]
            order.payment.save()
        except Exception as e:
            pass


@suspendingreceiver(
    post_save,
    sender="pizzas.FoodOrder",
)
def post_food_order_save(sender, instance, **kwargs):
    """ Create external invoice on payment creation."""
    if instance.payment is None:
        return
    if instance.payment.moneybird_invoice_id is not None:
        return
    
    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    contact_id = api.get("contacts/customer_id/34")["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = Contact.objects.get(member=instance.member).moneybird_id
        except:
            pass


    start_date = date(instance.food_event.event.start, "Y-m-d")
    project_name = f"{instance.food_event.event.title} [{start_date}]"
    project_id = services.get_project_id(api, project_name)
    
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


@suspendingreceiver(
    post_save,
    sender="registrations.Registration",
)
def post_entry_save(sender, instance, **kwargs):
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
                    "ledger_id": api.get("ledger_accounts")
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


@suspendingreceiver(
    post_save,
    sender="registrations.Renewal",
)
def post_renewal_save(sender, instance, **kwargs):
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
                    "ledger_id": api.get("ledger_accounts")
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


@suspendingreceiver(
    pre_delete,
    sender="payments.Payment",
)
def pre_payment_delete(sender, instance, **kwargs):
    """ Delete external invoice on payment deletion."""
    if instance.moneybird_invoice_id is None:
        print("No invoice to delete")
        return

    api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
    print(api.delete(f"external_sales_invoices/{instance.moneybird_invoice_id}"))
    if instance.moneybird_financial_statement_id is not None:
        try:
            api.patch(f"financial_statements/{instance.moneybird_financial_statement_id}", {
                "financial_statement": {
                    "financial_mutations_attributes": {
                        "0": {
                            "id": instance.moneybird_financial_mutation_id,
                            "_destroy": True
                        }
                    }
                }
            })
        except Administration.InvalidData:
            api.delete(f"financial_statements/{instance.moneybird_financial_statement_id}")