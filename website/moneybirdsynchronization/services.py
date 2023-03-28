from events.models.event import Event
from payments.models import Payment
from members.models import Member
from moneybirdsynchronization.models import Contact
from moneybirdsynchronization.administration import HttpsAdministration, Administration
from moneybirdsynchronization import emails
from thaliawebsite import settings
from django.template.defaultfilters import date

import datetime

class MoneybirdAPIService():

    def __init__(self):
        api = HttpsAdministration(settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID)
        self.api = api
    
    def update_contact(self, contact):
        if contact.moneybird_version is None:
            response = self.api.post("contacts", contact.to_moneybird())
            contact.moneybird_id = response["id"]
            contact.moneybird_version = response["version"]
            contact.save()
        else:
            response = self.api.patch("contacts/{contact.moneybird_id}", contact.to_moneybird())
            contact.moneybird_version = response["version"]
            contact.save()

    def get_financial_account_id(self, identifier):
        for financial_account in self.api.get("financial_accounts"):
            if financial_account["identifier"] == identifier:
                return financial_account["id"]


    def get_project_id(self, name):
        for project in self.api.get("projects"):
            if project["name"] == name:
                return project["id"]
            
        return self.api.post("projects", {"project": {"name": name}})["id"]


    def get_contribution_ledger_id(self):
        for ledger in self.api.get("ledger_accounts"):
            if ledger["name"] == "Contribution":
                return ledger["id"]
        return None


    def link_transaction_to_financial_account(self, account_id, new_cash_payments):
        financial_mutations_attributes = []
        if account_id is None:
            return
        
        for instance in new_cash_payments:
            payment_response = self.api.post(f"external_sales_invoices/{instance.moneybird_invoice_id}/payments", 
                {"payment": {
                    "payment_date": instance.created_at.strftime("%Y-%m-%d"),
                    "price": str(instance.amount),
                    "financial_account_id": account_id, 
                    "invoice_id": instance.moneybird_invoice_id,
                    }
                }
            )

            financial_mutations_attributes.append({
                        "date": instance.created_at.strftime("%Y-%m-%d"),
                        "amount": str(instance.amount),
                        "message": instance.topic,
                    })
        
        if len(financial_mutations_attributes) > 0:
            statement_response = self.api.post("financial_statements",
                {"financial_statement": {
                    "financial_account_id": account_id,
                    "reference": f"Card payments {datetime.date.today()}",
                    "financial_mutations_attributes": financial_mutations_attributes
                    }
                }
            )

            for x in range(len(new_cash_payments)):
                instance = new_cash_payments[x]
                instance.moneybird_financial_statement_id = statement_response["id"]
                instance.moneybird_financial_mutation_id = statement_response["financial_mutations"][x]["id"]
                instance.save()

                mutation_response = self.api.patch(f"financial_mutations/{instance.moneybird_financial_mutation_id}/link_booking",{
                        "booking_type": "ExternalSalesInvoice",
                        "booking_id": instance.moneybird_invoice_id,
                        "price": str(instance.amount),
                        "description": instance.topic,
                    })


def push_thaliapay_batch(instance):
    apiservice = MoneybirdAPIService()
    payments = Payment.objects.filter(batch=instance)
    tpay_account_id = apiservice.get_financial_account_id("ThaliaPay")
    apiservice.link_transaction_to_financial_account(tpay_account_id, payments)


def update_contact(member):
    apiservice = MoneybirdAPIService()
    apiservice.update_contact(Contact.objects.get_or_create(member=member)[0])


def delete_contact(instance):
    apiservice = MoneybirdAPIService()
    member = Member.objects.get(profile=instance)
    contact = Contact.objects.get(member=member)
    apiservice.api.delete(f"contacts/{contact.moneybird_id}")
    contact.delete()


def register_event_registration_payment(instance):
    apiservice = MoneybirdAPIService()
    contact_id = apiservice.api.get(f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}")["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = Contact.objects.get(member=instance.member).moneybird_id
        except:
            pass


    start_date = date(instance.event.start, "Y-m-d")
    project_name = f"{instance.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)
    
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
        response = apiservice.api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Exception as e:
        emails.send_sync_error(e, instance.payment)


def register_shift_payments(orders, instance):
    try: 
        event = Event.objects.get(shifts=instance)
        start_date = date(event.start, "Y-m-d")
        project_name = f"{event.title} [{start_date}]"
    except:
        start_date = date(instance.start, "Y-m-d")
        project_name = f"{instance.__str__()} [{start_date}]"
    
    apiservice = MoneybirdAPIService()
    project_id = apiservice.get_project_id(project_name)

    for order in orders:
        contact_id = apiservice.api.get(f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}")["id"]
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
            response = apiservice.api.post("external_sales_invoices", invoice_info)
            order.payment.moneybird_invoice_id = response["id"]
            order.payment.save()
        except Exception as e:
            emails.send_sync_error(e, instance.payment)


def register_food_order_payment(instance):
    apiservice = MoneybirdAPIService()
    contact_id = apiservice.api.get(f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}")["id"]
    if instance.payment.paid_by is not None:
        try:
            contact_id = Contact.objects.get(member=instance.member).moneybird_id
        except:
            pass


    start_date = date(instance.food_event.event.start, "Y-m-d")
    project_name = f"{instance.food_event.event.title} [{start_date}]"
    project_id = apiservice.get_project_id(project_name)
    
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
        response = apiservice.api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Exception as e:
        emails.send_sync_error(e, instance.payment)


def register_contribution_payment(instance):
    apiservice = MoneybirdAPIService()
    contact_id = apiservice.api.get(f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_ID}")["id"]
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
                    "ledger_id": apiservice.api.get("ledger_accounts")
                },
            ],
        }
    }

    try:
        response = apiservice.api.post("external_sales_invoices", invoice_info)
        instance.payment.moneybird_invoice_id = response["id"]
        instance.payment.save()
    except Exception as e:
        emails.send_sync_error(e, instance.payment)


def delete_payment(instance):
    apiservice = MoneybirdAPIService()
    apiservice.api.delete(f"external_sales_invoices/{instance.moneybird_invoice_id}")
    if instance.moneybird_financial_statement_id is not None:
        try:
            apiservice.api.patch(f"financial_statements/{instance.moneybird_financial_statement_id}", {
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
            apiservice.api.delete(f"financial_statements/{instance.moneybird_financial_statement_id}")