"""Registers admin interfaces for the models defined in this module."""

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import MerchandiseItem


@admin.register(MerchandiseItem)
class MerchandiseItemAdmin(ModelAdmin):
    """This manages the admin interface for the model items."""

    #: Included fields in the admin interface
    fields = (
        "name",
        "price",
        "stock_value",
        "description",
        "image",
    )
    search_fields = ("name", "description")
    list_display = ("name", "price", "stock_value")
    list_filter = ("name", "price", "stock_value")
