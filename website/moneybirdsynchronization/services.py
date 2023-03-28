from payments.models import Payment
import datetime

def get_financial_account_id(api, name):
    for financial_account in api.get("financial_accounts"):
        if financial_account["identifier"] == name:
            return financial_account["id"]


def get_project_id(api, name):
    for project in api.get("projects"):
        if project["name"] == name:
            return project["id"]
        
    return api.post("projects", {"project": {"name": name}})["id"]


def get_contribution_ledger_id(api):
    for ledger in api.get("ledger_accounts"):
        if ledger["name"] == "Contribution":
            return ledger["id"]
    return None


def link_transaction_to_financial_account(api, cash_account_id, new_cash_payments):
    financial_mutations_attributes = []
    if cash_account_id is not None:
        for instance in new_cash_payments:
            payment_response = api.post("external_sales_invoices/{}/payments".format(instance.moneybird_invoice_id), 
                {"payment": {
                    "payment_date": instance.created_at.strftime("%Y-%m-%d"),
                    "price": str(instance.amount),
                    "financial_account_id": cash_account_id, 
                    "manual_payment_action": "payment_without_proof",
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
            statement_response = api.post("financial_statements",
                {"financial_statement": {
                    "financial_account_id": cash_account_id,
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

                mutation_response = api.patch("financial_mutations/{}/link_booking".format(instance.moneybird_financial_mutation_id),{
                        "booking_type": "ExternalSalesInvoice",
                        "booking_id": instance.moneybird_invoice_id,
                        "price": str(instance.amount),
                        "description": instance.topic,
                    })