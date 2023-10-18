from django.contrib import admin
from django.http import HttpRequest

from .models import MoneybirdContact, MoneybirdExternalInvoice, MoneybirdPayment


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

    readonly_fields = ("member",)

    search_fields = ("member__first_name", "member__last_name", "moneybird_id")

    def get_readonly_fields(self, request: HttpRequest, obj: MoneybirdContact = None):
        if not obj:
            return ()
        return super().get_readonly_fields(request, obj)


@admin.register(MoneybirdExternalInvoice)
class MoneybirdExternalInvoiceAdmin(admin.ModelAdmin):
    """Manage moneybird external invoices."""

    list_display = (
        "payable_object",
        "payable_model",
        "moneybird_invoice_id",
    )

    fields = (
        "payable_object",
        "payable_model",
        "moneybird_invoice_id",
    )

    readonly_fields = ("payable_object",)

    search_fields = (
        "payable_model__app_label",
        "payable_model__model",
        "moneybird_invoice_id",
    )

    def get_readonly_fields(
        self, request: HttpRequest, obj: MoneybirdExternalInvoice = None
    ):
        if not obj:
            return ()
        return super().get_readonly_fields(request, obj)


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

    readonly_fields = ("payment",)

    search_fields = (
        "payment__amount",
        "moneybird_financial_mutation_id",
        "moneybird_financial_statement_id",
    )

    def get_readonly_fields(self, request: HttpRequest, obj: MoneybirdPayment = None):
        if not obj:
            return ()
        return super().get_readonly_fields(request, obj)
