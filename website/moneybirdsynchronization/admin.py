from django.contrib import admin

from .models import MoneybirdContact, MoneybirdExternalInvoice, PushedThaliaPayBatch


@admin.register(MoneybirdContact)
class MoneybirdContactAdmin(admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = ("member", "moneybird_id")


@admin.register(MoneybirdExternalInvoice)
class MoneybirdExternalInvoiceAdmin(admin.ModelAdmin):
    list_display = ("payment",)


@admin.register(PushedThaliaPayBatch)
class PushedThaliaPayBatchAdmin(admin.ModelAdmin):
    list_display = ("batch", "pushed")
