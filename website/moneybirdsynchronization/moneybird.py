import datetime

from moneybirdsynchronization.administration import Administration, HttpsAdministration
from moneybirdsynchronization.models import MoneybirdContact

from thaliawebsite import settings


class MoneybirdAPIService:
    def __init__(self, administration_id, api_key):
        self.__api = HttpsAdministration(api_key, administration_id)

    def add_contact(self, contact):
        return self.__api.post("contacts", contact.to_moneybird())

    def update_contact(self, contact):
        if contact.moneybird_version is None:
            response = self.__api.post("contacts", contact.to_moneybird())
            contact.moneybird_id = response["id"]
            contact.moneybird_version = response["version"]
            contact.save()
        else:
            response = self.__api.patch(
                "contacts/{contact.moneybird_id}", contact.to_moneybird()
            )
            contact.moneybird_version = response["version"]
            contact.save()

    def delete_contact(self, contact):
        self.__api.delete(f"contacts/{contact.moneybird_id}")
        contact.delete()

    def delete_moneybird_customer(self, id):
        self.__api.delete(f"contacts/{id}")

    def get_contact_id_by_customer(self, instance):
        contact_id = self.__api.get(
            f"contacts/customer_id/{settings.MONEYBIRD_UNKOWN_PAYER_CONTACT_ID}"
        )["id"]
        if instance.payment.paid_by is not None:
            try:
                contact_id = MoneybirdContact.objects.get(
                    member=instance.member
                ).moneybird_id
            except MoneybirdContact.DoesNotExist:
                pass
        return contact_id

    def get_project_id(self, name):
        for project in self.__api.get("projects"):
            if project["name"] == name:
                return project["id"]

        return self.__api.post("projects", {"project": {"name": name}})["id"]

    def create_external_sales_invoice(self, invoice_info):
        return self.__api.post("external_sales_invoices", invoice_info)

    def create_external_sales_info(
        self, contact_id, payment, project_id=None, contribution=False
    ):
        if contribution:
            return {
                "external_sales_invoice": {
                    "contact_id": contact_id,
                    "reference": str(payment.id),
                    "date": payment.created_at.strftime("%Y-%m-%d"),
                    "source_url": settings.BASE_URL + payment.get_admin_url(),
                    "currency": "EUR",
                    "prices_are_incl_tax": True,
                    "details_attributes": [
                        {
                            "description": payment.topic,
                            "price": str(payment.amount),
                            "ledger_id": self.__api.get("ledger_accounts"),
                        },
                    ],
                }
            }
        if project_id is not None:
            return {
                "external_sales_invoice": {
                    "contact_id": contact_id,
                    "reference": str(payment.id),
                    "date": payment.created_at.strftime("%Y-%m-%d"),
                    "source_url": settings.BASE_URL + payment.get_admin_url(),
                    "currency": "EUR",
                    "prices_are_incl_tax": True,
                    "details_attributes": [
                        {
                            "description": payment.topic,
                            "price": str(payment.amount),
                            "project_id": project_id,
                        },
                    ],
                }
            }

        return RuntimeError("No project_id provided")

    def link_transaction_to_financial_account(self, account_id, new_cash_payments):
        financial_mutations_attributes = []
        if account_id is None:
            return

        for payment in new_cash_payments:
            payment_response = self.__api.post(
                f"external_sales_invoices/{payment.moneybird_external_invoice.moneybird_invoice_id}/payments",
                {
                    "payment": {
                        "payment_date": payment.created_at.strftime("%Y-%m-%d"),
                        "price": str(payment.amount),
                        "financial_account_id": account_id,
                        "invoice_id": payment.moneybird_external_invoice.moneybird_invoice_id,
                    }
                },
            )

            financial_mutations_attributes.append(
                {
                    "date": payment.created_at.strftime("%Y-%m-%d"),
                    "amount": str(payment.amount),
                    "message": payment.topic,
                }
            )

        if len(financial_mutations_attributes) > 0:
            statement_response = self.__api.post(
                "financial_statements",
                {
                    "financial_statement": {
                        "financial_account_id": account_id,
                        "reference": f"Card payments {datetime.date.today()}",
                        "financial_mutations_attributes": financial_mutations_attributes,
                    }
                },
            )
            for x, payment in enumerate(new_cash_payments):
                payment.moneybird_external_invoice.moneybird_financial_statement_id = (
                    statement_response["id"]
                )
                payment.moneybird_external_invoice.moneybird_financial_mutation_id = (
                    statement_response["financial_mutations"][x]["id"]
                )
                payment.moneybird_external_invoice.save()

                mutation_response = self.__api.patch(
                    f"financial_mutations/{payment.moneybird_external_invoice.moneybird_financial_mutation_id}/link_booking",
                    {
                        "booking_type": "ExternalSalesInvoice",
                        "booking_id": payment.moneybird_external_invoice.moneybird_invoice_id,
                        "price": str(payment.amount),
                        "description": payment.topic,
                    },
                )

    def delete_external_invoice(self, instance):
        self.__api.delete(f"external_sales_invoices/{instance.moneybird_invoice_id}")
        if instance.moneybird_financial_statement_id is not None:
            try:
                self.__api.patch(
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
                self.__api.delete(
                    f"financial_statements/{instance.moneybird_financial_statement_id}"
                )
