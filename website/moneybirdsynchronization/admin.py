from django.contrib import admin

from .models import MoneybirdContact


@admin.register(MoneybirdContact)
class MoneybirdContactAdmin(admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = ("member", "moneybird_id")
