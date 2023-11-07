"""Registers admin interfaces for the models defined in this module."""

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import MerchandiseItem, MerchandiseProduct


class MerchandiseProductInline(admin.TabularInline):
    """Inline admin interface for the merchandise products."""

    model = MerchandiseProduct
    extra = 0


@admin.register(MerchandiseItem)
class MerchandiseItemAdmin(ModelAdmin):
    """This manages the admin interface for the model items."""

    #: Included fields in the admin interface
    fields = (
        "name",
        "price",
        "description",
        "image",
    )
    search_fields = ("name", "description")
    list_display = ("name", "price")
    list_filter = ("name", "price")

    inlines = [MerchandiseProductInline]
