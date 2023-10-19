from django.contrib import admin

from .models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
    MoneybirdSalesInvoice,
)


@admin.register(MoneybirdContact)
class MoneybirdContactAdmin(admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = ("member", "moneybird_id")


@admin.register(MoneybirdExternalInvoice)
class MoneybirdExternalInvoiceAdmin(admin.ModelAdmin):
    list_display = ("payable_object",)


@admin.register(MoneybirdSalesInvoice)
class MoneybirdSalesInvoiceAdmin(admin.ModelAdmin):
    list_display = ("payable_object",)


@admin.register(MoneybirdPayment)
class MoneybirdPaymentAdmin(admin.ModelAdmin):
    list_display = ("payment",)
