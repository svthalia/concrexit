from decimal import Decimal
from typing import Union

from django.conf import settings

from moneybirdsynchronization.administration import HttpsAdministration


class MoneybirdAPIService:
    def __init__(self, administration_id, api_key):
        self._administration = HttpsAdministration(api_key, administration_id)

    def create_contact(self, contact_data):
        return self._administration.post("contacts", contact_data)

    def update_contact(self, contact_id, contact_data):
        return self._administration.patch(f"contacts/{contact_id}", contact_data)

    def delete_contact(self, contact_id):
        self._administration.delete(f"contacts/{contact_id}")

    def create_project(self, project_data):
        return self._administration.post("projects", project_data)

    def create_external_sales_invoice(self, invoice_data):
        return self._administration.post("external_sales_invoices", invoice_data)

    def update_external_sales_invoice(self, invoice_id, invoice_data):
        return self._administration.patch(
            f"external_sales_invoices/{invoice_id}", invoice_data
        )

    def delete_external_invoice(self, invoice_id):
        self._administration.delete(f"external_sales_invoices/{invoice_id}")

    def register_external_invoice_payment(self, invoice_id, payment_data):
        return self._administration.post(
            f"external_sales_invoices/{invoice_id}/payments", payment_data
        )

    def delete_external_invoice_payment(self, invoice_id, payment_id):
        self._administration.delete(
            f"external_sales_invoices/{invoice_id}/payments/{payment_id}"
        )

    def create_sales_invoice(self, invoice_data):
        return self._administration.post("sales_invoices", invoice_data)

    def update_sales_invoice(self, invoice_id, invoice_data):
        return self._administration.patch(f"sales_invoices/{invoice_id}", invoice_data)

    def delete_invoice(self, invoice_id):
        self._administration.delete(f"sales_invoices/{invoice_id}")

    def register_invoice_payment(self, invoice_id, payment_data):
        return self._administration.post(
            f"sales_invoices/{invoice_id}/payments", payment_data
        )

    def delete_invoice_payment(self, invoice_id, payment_id):
        self._administration.delete(
            f"sales_invoices/{invoice_id}/payments/{payment_id}"
        )

    def create_financial_statement(self, statement_data):
        return self._administration.post("financial_statements", statement_data)

    def update_financial_statement(self, statement_id, statement_data):
        return self._administration.patch(
            f"financial_statements/{statement_id}", statement_data
        )

    def delete_financial_statement(self, statement_id):
        return self._administration.delete(f"financial_statements/{statement_id}")

    def link_mutation_to_booking(
        self,
        mutation_id: int,
        booking_id: int,
        price_base: Union[Decimal, str],
        booking_type: str = "ExternalSalesInvoice",
    ):
        return self._administration.patch(
            f"financial_mutations/{mutation_id}/link_booking",
            {
                "booking_type": booking_type,
                "booking_id": booking_id,
                "price_base": price_base,
            },
        )

    def get_financial_mutation_info(self, mutation_id):
        return self._administration.get(f"financial_mutations/{mutation_id}")

    def unlink_mutation_from_booking(
        self, mutation_id: int, booking_id: int, booking_type: str = "Payment"
    ):
        return self._administration.delete(
            f"financial_mutations/{mutation_id}/unlink_booking",
            {"booking_type": booking_type, "booking_id": booking_id},
        )

    def send_invoice(self, invoice_id):
        return self._administration.patch(
            f"sales_invoices/{invoice_id}/send_invoice",
            {"sales_invoice_sending": {"delivery_method": "Manual"}},
        )

    def get_invoice_info(self, invoice_id):
        return self._administration.get(f"sales_invoices/{invoice_id}")


def get_moneybird_api_service():
    if (
        settings.MONEYBIRD_ADMINISTRATION_ID is None
        or settings.MONEYBIRD_API_KEY is None
    ):
        raise RuntimeError("Moneybird API key or administration ID not set")
    return MoneybirdAPIService(
        administration_id=settings.MONEYBIRD_ADMINISTRATION_ID,
        api_key=settings.MONEYBIRD_API_KEY,
    )
