from import_export import resources
from import_export.fields import Field

from payments.models import BankAccount, Payment


class PaymentResource(resources.ModelResource):
    created_at = Field(attribute="created_at", column_name="Created")
    amount = Field(attribute="amount", column_name="Amount")
    payment_type = Field(column_name="Type")
    processed_by = Field(column_name="Processor")
    payer_id = Field(column_name="Payer id")
    paid_by = Field(column_name="Payer name")
    notes = Field(attribute="notes", column_name="Notes")

    class Meta:
        model = Payment
        fields = (
            "created_at",
            "amount",
            "payment_type",
            "processed_by",
            "payer_id",
            "paid_by",
            "notes",
        )
        export_order = fields

    def dehydrate_processed_by(self, payment):
        if payment.processed_by:
            return payment.processed_by.get_full_name()
        return "-"

    def dehydrate_payer_id(self, payment):
        if payment.paid_by:
            return payment.paid_by.pk
        return "-"

    def dehydrate_paid_by(self, payment):
        if payment.paid_by:
            return payment.paid_by.get_full_name()
        return "-"

    def dehydrate_payment_type(self, payment):
        return payment.get_type_display()


class BankAccountResource(resources.ModelResource):
    created_at = Field(attribute="created_at", column_name="Created")
    name = Field(attribute="name", column_name="Name")
    mandate_no = Field(attribute="mandate_no", column_name="Reference")
    iban = Field(attribute="iban", column_name="IBAN")
    bic = Field(attribute="bic", column_name="BIC")
    valid_from = Field(attribute="valid_from", column_name="Valid from")
    valid_until = Field(attribute="valid_until", column_name="Valid until")
    signature = Field(attribute="signature", column_name="Signature")

    class Meta:
        model = BankAccount
        fields = (
            "created_at",
            "name",
            "mandate_no",
            "iban",
            "bic",
            "valid_from",
            "valid_until",
            "signature",
        )
        export_order = fields
