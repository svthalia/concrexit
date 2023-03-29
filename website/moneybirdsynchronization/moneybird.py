import datetime

from moneybirdsynchronization.administration import HttpsAdministration


class MoneybirdAPIService:
    def __init__(self, administration_id, api_key):
        self.api = HttpsAdministration(api_key, administration_id)

    def update_contact(self, contact):
        if contact.moneybird_version is None:
            response = self.api.post("contacts", contact.to_moneybird())
            contact.moneybird_id = response["id"]
            contact.moneybird_version = response["version"]
            contact.save()
        else:
            response = self.api.patch(
                "contacts/{contact.moneybird_id}", contact.to_moneybird()
            )
            contact.moneybird_version = response["version"]
            contact.save()

    def get_financial_account_id(self, identifier):
        for financial_account in self.api.get("financial_accounts"):
            if financial_account["identifier"] == identifier:
                return financial_account["id"]
        return None

    def get_project_id(self, name):
        for project in self.api.get("projects"):
            if project["name"] == name:
                return project["id"]

        return self.api.post("projects", {"project": {"name": name}})["id"]

    def link_transaction_to_financial_account(self, account_id, new_cash_payments):
        financial_mutations_attributes = []
        if account_id is None:
            return

        for instance in new_cash_payments:
            payment_response = self.api.post(
                f"external_sales_invoices/{instance.moneybird_invoice_id}/payments",
                {
                    "payment": {
                        "payment_date": instance.created_at.strftime("%Y-%m-%d"),
                        "price": str(instance.amount),
                        "financial_account_id": account_id,
                        "invoice_id": instance.moneybird_invoice_id,
                    }
                },
            )

            financial_mutations_attributes.append(
                {
                    "date": instance.created_at.strftime("%Y-%m-%d"),
                    "amount": str(instance.amount),
                    "message": instance.topic,
                }
            )

        if len(financial_mutations_attributes) > 0:
            statement_response = self.api.post(
                "financial_statements",
                {
                    "financial_statement": {
                        "financial_account_id": account_id,
                        "reference": f"Card payments {datetime.date.today()}",
                        "financial_mutations_attributes": financial_mutations_attributes,
                    }
                },
            )
            for x, instance in enumerate(new_cash_payments):
                instance.moneybird_financial_statement_id = statement_response["id"]
                instance.moneybird_financial_mutation_id = statement_response[
                    "financial_mutations"
                ][x]["id"]
                instance.save()

                mutation_response = self.api.patch(
                    f"financial_mutations/{instance.moneybird_financial_mutation_id}/link_booking",
                    {
                        "booking_type": "ExternalSalesInvoice",
                        "booking_id": instance.moneybird_invoice_id,
                        "price": str(instance.amount),
                        "description": instance.topic,
                    },
                )
