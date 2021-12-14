"""Registers admin interfaces for the models defined in this module."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db import models
from django.forms import CheckboxSelectMultiple

from promotion.forms import RequestAdminForm

from .models import PromotionChannel, PromotionRequest


@admin.register(PromotionRequest)
class PromotionRequestAdmin(admin.ModelAdmin):
    """This manages the admin interface for the model items."""
    list_display = (
        "event", 
        "publish_date", 
        "channel",
        "assigned_to",
        "status"
    )

    form = RequestAdminForm

    #: Included fields in the admin interface
    fields = (
        "event",
        "publish_date",
        "channel",
        "assigned_to",
        "status",
        "drive_folder"
    )

    formfield_overrides = {
        models.ManyToManyField: {
            'widget': CheckboxSelectMultiple
        },
    }


@admin.register(PromotionChannel)
class PromotionChannelAdmin(ModelAdmin):
    list_display = (
        "name",
    )

    fields = (
        "name",
    )