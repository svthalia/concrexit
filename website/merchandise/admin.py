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
        "description",
        "image",
    )
