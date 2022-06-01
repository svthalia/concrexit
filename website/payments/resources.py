from import_export import resources
from import_export.fields import Field

from .models import Payment


class PaymentResource(resources.ModelResource):
    created_at = Field(attribute="created_at", column_name="Created")
    amount = Field(attribute="amount", column_name="Amount")
    type = Field(column_name="Type")
    processed_by = Field(column_name="Processor")
    payer_id = Field(column_name="Payer id")
    paid_by = Field(column_name="Payer name")
    notes = Field(attribute="notes", column_name="Notes")

    class Meta:
        model = Payment
        fields = (
            "created_at",
            "amount",
            "type",
            "processed_by",
            "payer_id",
            "paid_by",
            "notes",
        )
        export_order = (
            "created_at",
            "amount",
            "type",
            "processed_by",
            "payer_id",
            "paid_by",
            "notes",
        )

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

    def dehydrate_type(self, payment):
        return payment.get_type_display()
