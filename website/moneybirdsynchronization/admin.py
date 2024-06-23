from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
    MoneybirdProject,
)


@admin.register(MoneybirdContact)
class MoneybirdContactAdmin(admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = (
        "member",
        "moneybird_id",
        "moneybird_sepa_mandate_id",
        "needs_synchronization",
    )

    list_filter = ("needs_synchronization",)

    fields = (
        "member",
        "moneybird_id",
        "moneybird_sepa_mandate_id",
        "needs_synchronization",
    )

    raw_id_fields = ("member",)

    search_fields = (
        "member__first_name",
        "member__last_name",
        "member__username",
        "member__email",
        "member__id",
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

    def payable_object(self, obj: MoneybirdExternalInvoice) -> str:
        payable_object = obj.payable_object
        if payable_object:
            return format_html(
                "<a href='{}'>{}</a>",
                reverse(
                    f"admin:{payable_object._meta.app_label}_{payable_object._meta.model_name}_change",
                    args=[payable_object.pk],
                ),
                payable_object,
            )
        return "None"


@admin.register(MoneybirdPayment)
class MoneybirdPaymentAdmin(admin.ModelAdmin):
    """Manage moneybird payments."""

    list_display = (
        "payment_topic",
        "amount",
        "paid_by",
        "payment_type",
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
        "payment__topic",
        "payment__paid_by__username",
        "moneybird_financial_mutation_id",
        "moneybird_financial_statement_id",
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ()
        return ("payment",)

    def payment_type(self, obj):
        return obj.payment.type

    def payment_topic(self, obj):
        return obj.payment.topic

    def paid_by(self, obj):
        return obj.payment.paid_by

    def amount(self, obj):
        return obj.payment.amount


@admin.register(MoneybirdProject)
class MoneybirdProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "moneybird_id",
    )

    search_fields = ("name", "moneybird_id")
