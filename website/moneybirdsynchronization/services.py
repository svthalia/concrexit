from payments.models import Payment

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


def link_transaction_to_financial_account(api, instance, response, project_id):
    payment_identifiers = {
        Payment.TPAY: "ThaliaPay",
        Payment.CASH: "cashtanje",
        Payment.CARD: "pin"
    }

    if instance.payment.type != Payment.WIRE:
        account_id = get_financial_account_id(api, payment_identifiers[instance.payment.type])
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
            instance.payment.moneybird_financial_statement_id = statement_response["id"]
            instance.payment.moneybird_financial_mutation_id = statement_response["financial_mutations"][0]["id"]
            instance.payment.save()

            if project_id is not None:
                mutation_response = api.patch("financial_mutations/{}/link_booking".format(statement_response["financial_mutations"][0]["id"]),{
                    "booking_type": "ExternalSalesInvoice",
                    "booking_id": response["id"],
                    "price": str(instance.payment.amount),
                    "description": instance.payment.topic,
                    "project_id": project_id,
                })
            else:
                mutation_response = api.patch("financial_mutations/{}/link_booking".format(statement_response["financial_mutations"][0]["id"]),{
                    "booking_type": "ExternalSalesInvoice",
                    "booking_id": response["id"],
                    "price": str(instance.payment.amount),
                    "description": instance.payment.topic,
                })