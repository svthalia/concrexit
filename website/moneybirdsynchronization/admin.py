from django.contrib import admin

from .models import Contact
from moneybird.admin import MoneybirdResourceModelAdminMixin

@admin.register(Contact)
class ContactAdmin(MoneybirdResourceModelAdminMixin, admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = ("first_name", "last_name")