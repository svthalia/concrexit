"""Registers admin interfaces for the models defined in this module."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from events.services import is_organiser
from promotion.forms import PromotionRequestForm

from .models import PromotionChannel, PromotionRequest


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
    actions = ["mark_not_started", "mark_started", "mark_finished", "mark_published"]

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.event and is_organiser(request.member, obj.event):
            return True
        return super().has_change_permission(request, obj)

    def mark_not_started(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.NOT_STARTED)

    mark_not_started.short_description = "Mark requests as not started"

    def mark_started(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.STARTED)

    mark_started.short_description = "Mark requests as started"

    def mark_finished(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.FINISHED)

    mark_finished.short_description = "Mark requests as finished"

    def mark_published(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.PUBLISHED)

    mark_published.short_description = "Mark requests as published"

    @staticmethod
    def _change_published(queryset, status):
        queryset.update(status=status)


@admin.register(PromotionChannel)
class PromotionChannelAdmin(ModelAdmin):
    pass
