"""Registers admin interfaces for the models defined in this module."""
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from promotion.forms import PromotionRequestForm
from events.services import is_organiser

from .models import PromotionChannel, PromotionRequest


@admin.register(PromotionRequest)
class PromotionRequestAdmin(ObjectActionsMixin, admin.ModelAdmin):
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

    @object_action(
        label=_("Mark not started"),
        permission="promotion.change_promotionrequest",
        condition=lambda _, obj: not obj.status == PromotionRequest.NOT_STARTED,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Marked as not started"),
        perform_after_saving=True,
    )
    def not_started(self, request, obj):
        obj.status = PromotionRequest.NOT_STARTED
        obj.save()
        messages.success(request, _("Marked as not started."))
        return True

    @object_action(
        label=_("Mark started"),
        permission="promotion.change_promotionrequest",
        condition=lambda _, obj: not obj.status == PromotionRequest.STARTED,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Marked as started"),
        perform_after_saving=True,
    )
    def started(self, request, obj):
        obj.status = PromotionRequest.STARTED
        obj.save()
        messages.success(request, _("Marked as started."))
        return True

    @object_action(
        label=_("Mark finished"),
        permission="promotion.change_promotionrequest",
        condition=lambda _, obj: not obj.status == PromotionRequest.FINISHED,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Marked as finished"),
        perform_after_saving=True,
    )
    def finished(self, request, obj):
        obj.status = PromotionRequest.FINISHED
        obj.save()
        messages.success(request, _("Marked as finished."))
        return True

    @object_action(
        label=_("Mark published"),
        permission="promotion.change_promotionrequest",
        condition=lambda _, obj: not obj.status == PromotionRequest.PUBLISHED,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Marked as published"),
        perform_after_saving=True,
    )
    def published(self, request, obj):
        obj.status = PromotionRequest.PUBLISHED
        obj.save()
        messages.success(request, _("Marked as published."))
        return True

    object_actions_after_related_objects = [
        "not_started",
        "started",
        "finished",
        "published",
    ]

    readonly_fields = ("status",)

    @staticmethod
    def _change_published(queryset, status):
        queryset.update(status=status)


@admin.register(PromotionChannel)
class PromotionChannelAdmin(ModelAdmin):
    pass
