"""The admin interfaces registered by the pushnotifications package."""
from django.apps import apps
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin, helpers
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from events.decorators import organiser_only
from events.models import Event

from .forms import EventMessageForm
from .models import Category, Device, Message, ScheduledMessage


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


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
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


@admin.register(Message)
class MessageAdmin(ModelAdmin):
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

    def change_view(self, request, object_id, form_url="", **kwargs):
        obj = Message.objects.filter(id=object_id)[0]
        return super().change_view(request, object_id, form_url, {"message": obj})


@admin.register(ScheduledMessage)
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


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(organiser_only, name="dispatch")
class EventMessageView(FormView):
    """View used to create a pushnotification for all users registered to an event."""

    form_class = EventMessageForm
    template_name = "admin/pushnotifications/event_message_form.html"
    admin = None
    event = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.admin.admin_site.each_context(self.request),
                "add": False,
                "change": True,
                "has_view_permission": True,
                "has_add_permission": False,
                "has_change_permission": self.request.user.has_perms(
                    ["events.change_event"]
                ),
                "has_delete_permission": False,
                "has_editable_inline_admin_formsets": False,
                "app_label": "events",
                "opts": self.event._meta,
                "is_popup": False,
                "save_as": False,
                "save_on_top": False,
                "original": self.event,
                "obj_id": self.event.pk,
                "title": _("Send push notification"),
                "adminform": helpers.AdminForm(
                    context["form"],
                    ((None, {"fields": context["form"].fields.keys()}),),
                    {},
                ),
            }
        )
        return context

    def form_valid(self, form):
        values = form.cleaned_data
        if not values["url"]:
            values["url"] = f"{settings.BASE_URL}{self.event.get_absolute_url()}"

        message = Message(
            title=values["title"],
            body=values["body"],
            url=values["url"],
            category=Category.objects.get(key=Category.EVENT),
        )
        message.save()
        message.users.set([r.member for r in self.event.participants if r.member])
        message.send()

        messages.success(self.request, _("Message sent successfully."))

        if "_save" in self.request.POST:
            return redirect("admin:events_event_details", self.event.pk)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)


# Announcements also overrides the EventAdmin. We need to override the latest.
if apps.is_installed("announcements"):
    from announcements.admin import EventAdmin as BaseEventAdmin
else:
    from events.admin import EventAdmin as BaseEventAdmin  # pylint: disable=C0412


class EventAdmin(BaseEventAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/message/",
                self.admin_site.admin_view(EventMessageView.as_view(admin=self)),
                name="events_event_message",
            ),
        ]
        return custom_urls + urls


# Unregister the original EventAdmin and register
# the new one with pushnotifications functionality.
admin.site.unregister(Event)
admin.site.register(Event, EventAdmin)
