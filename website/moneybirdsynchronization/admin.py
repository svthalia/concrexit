from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter

from .models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
    MoneybirdSalesInvoice,
)


@admin.register(MoneybirdContact)
class MoneybirdContactAdmin(admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = (
        "member",
        "moneybird_id",
        "moneybird_sepa_mandate_id",
    )

    fields = (
        "member",
        "moneybird_id",
        "moneybird_sepa_mandate_id",
    )

    raw_id_fields = ("member",)

    search_fields = (
        "member__first_name",
        "member__last_name",
        "member__username",
        "member__email",
        "moneybird_id",
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ()
        return ("member",)


@admin.register(MoneybirdExternalInvoice)
class MoneybirdExternalInvoiceAdmin(admin.ModelAdmin):
    """Manage moneybird external invoices."""

    list_display = (
        "payable_object",
        "payable_model",
        "moneybird_invoice_id",
        "needs_synchronization",
        "needs_deletion",
    )

    fields = (
        "payable_object",
        "payable_model",
        "object_id",
        "moneybird_invoice_id",
        "needs_synchronization",
        "needs_deletion",
    )

    readonly_fields = ("payable_object", "needs_synchronization", "needs_deletion")

    search_fields = (
        "payable_model__app_label",
        "payable_model__model",
        "moneybird_invoice_id",
    )

    list_filter = (
        "needs_synchronization",
        "needs_deletion",
        ("payable_model", RelatedOnlyFieldListFilter),
    )


@admin.register(MoneybirdSalesInvoice)
class MoneybirdSalesInvoiceAdmin(admin.ModelAdmin):
    list_display = ("payable_object",)


@admin.register(MoneybirdPayment)
class MoneybirdPaymentAdmin(admin.ModelAdmin):
    """Manage moneybird payments."""

    list_display = (
        "payment",
        "moneybird_financial_statement_id",
        "moneybird_financial_mutation_id",
    )

    fields = (
        "payment",
        "moneybird_financial_statement_id",
        "moneybird_financial_mutation_id",
    )

    raw_id_fields = ("payment",)

    search_fields = (
        "payment__amount",
        "moneybird_financial_mutation_id",
        "moneybird_financial_statement_id",
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ()
        return ("payment",)
