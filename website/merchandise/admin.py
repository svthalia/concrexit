"""Registers admin interfaces for the models defined in this module."""
from django.contrib import admin

from utils.translation import TranslatedModelAdmin

from .models import MerchandiseItem


@admin.register(MerchandiseItem)
class MerchandiseItemAdmin(TranslatedModelAdmin):
    """This manages the admin interface for the model items."""

    #: Included fields in the admin interface
    fields = (
        "name",
        "price",
        "description",
        "image",
    )
