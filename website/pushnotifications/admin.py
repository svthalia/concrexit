"""The admin interfaces registered by the pushnotifications package"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from pushnotifications import models
from pushnotifications.models import Message
from utils.translation import TranslatedModelAdmin


class MessageSentFilter(admin.SimpleListFilter):
    """Filter the push notifications on whether they are sent or not"""

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
        elif self.value() == "0":
            return queryset.filter(sent__isnull=True)

        return queryset


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin):
    """Manage the devices"""

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

    def enable(self, request, queryset):
        queryset.update(active=True)

    enable.short_description = _("Enable selected devices")

    def disable(self, request, queryset):
        queryset.update(active=False)

    disable.short_description = _("Disable selected devices")

    def name(self, obj):
        return "{} ({})".format(obj.user.get_full_name(), obj.user.username)

    name.short_description = _("Name")
    name.admin_order_field = "user__first_name"


@admin.register(models.Message)
class MessageAdmin(TranslatedModelAdmin):
    """Manage normal messages"""

    list_display = ("title", "body", "category", "url", "sent", "success", "failure")
    filter_horizontal = ("users",)
    list_filter = (MessageSentFilter, "category")
    date_hierarchy = "sent"

    def get_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title_en",
                "body_en",
                "url",
                "category",
                "sent",
                "success",
                "failure",
            )
        return (
            "users",
            "title_en",
            "body_en",
            "url",
            "category",
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title_en",
                "body_en",
                "url",
                "category",
                "sent",
                "success",
                "failure",
            )
        return super().get_readonly_fields(request, obj)

    def change_view(self, request, object_id, form_url="", **kwargs):
        obj = Message.objects.filter(id=object_id)[0]
        return super().change_view(request, object_id, form_url, {"message": obj})


@admin.register(models.ScheduledMessage)
class ScheduledMessageAdmin(TranslatedModelAdmin):
    """Manage scheduled messages"""

    list_display = ("title", "body", "time", "category", "sent", "success", "failure")
    date_hierarchy = "time"
    filter_horizontal = ("users",)
    list_filter = (MessageSentFilter, "category")

    def get_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title_en",
                "body_en",
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
            "title_en",
            "body_en",
            "url",
            "category",
            "time",
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sent:
            return (
                "users",
                "title_en",
                "body_en",
                "url",
                "category",
                "sent",
                "success",
                "failure",
                "time",
                "executed",
            )
        return ("executed",)
