from django.contrib import admin

from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Manage moneybird contacts."""

    list_display = ("first_name", "last_name")
