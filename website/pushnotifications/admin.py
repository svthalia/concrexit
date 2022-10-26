"""The admin interfaces registered by the pushnotifications package."""
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from pushnotifications import models
from pushnotifications.models import Message


class MessageSentFilter(admin.SimpleListFilter):
    """Filter the push notifications on whether they are sent or not."""

    title = _("sent")
    parameter_name = "is_sent"

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        values = []

        if queryset.filter(sent__isnull=False).exists():
            values.append((1, _("Yes")))
        if queryset.filter(sent__isnull=True).exists():
            values.append((0, _("No")))

        return values

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(sent__isnull=False)
        if self.value() == "0":
            return queryset.filter(sent__isnull=True)
        return queryset


@admin.register(models.Device)
class DeviceAdmin(ObjectActionsMixin, admin.ModelAdmin):
    """Manage the devices."""

    list_display = ("name", "type", "active", "date_created")
    list_filter = ("active", "type")
    actions = ("enable", "disable")
    ordering = ("user__first_name",)
    search_fields = (
        "registration_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = ("active",)

    @object_action(
        label=_("Disable"),
        permission="pushnotifications.change_device",
        condition=lambda _, obj: obj.active,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Disabled"),
        perform_after_saving=True,
    )
    def disable_object_action(self, request, obj):
        obj.active = False
        obj.save()
        messages.success(request, _("Disabled device."))
        return redirect("admin:pushnotifications_device_change", obj.pk)

    @object_action(
        label=_("Enable"),
        permission="pushnotifications.change_device",
        condition=lambda _, obj: not obj.active,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Disabled"),
        perform_after_saving=True,
    )
    def enable_object_action(self, request, obj):
        obj.active = True
        obj.save()
        messages.success(request, _("Enabled device."))
        return redirect("admin:pushnotifications_device_change", obj.pk)

    object_actions_after_related_objects = [
        "disable_object_action",
        "enable_object_action",
    ]

    def enable(self, request, queryset):
        queryset.update(active=True)

    enable.short_description = _("Enable selected devices")

    def disable(self, request, queryset):
        queryset.update(active=False)

    disable.short_description = _("Disable selected devices")

    def name(self, obj):
        return f"{obj.user.get_full_name()} ({obj.user.username})"

    name.short_description = _("Name")
    name.admin_order_field = "user__first_name"


@admin.register(models.Message)
class MessageAdmin(ObjectActionsMixin, ModelAdmin):
    """Manage normal messages."""

    list_display = ("title", "body", "category", "url", "sent", "success", "failure")
    filter_horizontal = ("users",)
    list_filter = (MessageSentFilter, "category")
    date_hierarchy = "sent"

    def get_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title",
                "body",
                "url",
                "category",
                "sent",
                "success",
                "failure",
            )
        return (
            "users",
            "title",
            "body",
            "url",
            "category",
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title",
                "body",
                "url",
                "category",
                "sent",
                "success",
                "failure",
            )
        return super().get_readonly_fields(request, obj)

    @object_action(
        label=_("Send"),
        condition=lambda _, obj: not obj.sent,
        log_message=_("Sent"),
        perform_after_saving=True,
    )
    def send(self, request, obj):
        """Reverse the review status."""
        obj.send()
        return True

    object_actions_after_related_objects = [
        "send",
    ]


@admin.register(models.ScheduledMessage)
class ScheduledMessageAdmin(ModelAdmin):
    """Manage scheduled messages."""

    list_display = ("title", "body", "time", "category", "sent", "success", "failure")
    date_hierarchy = "time"
    filter_horizontal = ("users",)
    list_filter = (MessageSentFilter, "category")

    def get_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title",
                "body",
                "url",
                "category",
                "sent",
                "success",
                "failure",
                "time",
                "executed",
            )
        return (
            "users",
            "title",
            "body",
            "url",
            "category",
            "time",
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title",
                "body",
                "url",
                "category",
                "sent",
                "success",
                "failure",
                "time",
                "executed",
            )
        return ("executed",)
