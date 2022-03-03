"""Registers admin interfaces for the models defined in this module."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import PromotionChannel, PromotionRequest
from promotion.forms import PromotionRequestForm
from events.services import is_organiser

@admin.register(PromotionRequest)
class PromotionRequestAdmin(admin.ModelAdmin):
    """This manages the admin interface for the model items."""

    list_display = ("event", "publish_date", "channel", "assigned_to", "status")
    list_filter = (
        "publish_date",
        "assigned_to",
        "status",
    )
    date_hierarchy = "publish_date"
    form = PromotionRequestForm

    def has_change_permission(self, request, obj=None):
        if obj is not None and not is_organiser(request.member, obj.event):
            return False
        return super().has_change_permission(request, obj)


@admin.register(PromotionChannel)
class PromotionChannelAdmin(ModelAdmin):
    list_display = (
        "name",
    )

    fields = (
        "name",
    )
