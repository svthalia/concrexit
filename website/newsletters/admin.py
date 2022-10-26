"""Registers admin interfaces for the newsletters module."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from newsletters.models import Newsletter, NewsletterEvent, NewsletterItem
from . import services
from .forms import NewsletterEventForm


class NewsletterItemInline(admin.StackedInline):
    """The inline for the text items in the newsletter."""

    model = NewsletterItem
    extra = 0
    fields = (
        "order",
        "title",
        "url",
        "description",
    )


class NewsletterEventInline(admin.StackedInline):
    """The inline for the event items in the newsletter."""

    form = NewsletterEventForm
    model = NewsletterEvent
    extra = 0


@admin.register(Newsletter)
class NewsletterAdmin(ObjectActionsMixin, ModelAdmin):
    """Manage the newsletters."""

    #: available fields in the admin overview list
    list_display = (
        "title",
        "date",
        "send_date",
        "sent",
    )
    #: available inlines in the admin change form
    inlines = (
        NewsletterItemInline,
        NewsletterEventInline,
    )
    #: available fieldsets in the admin change form
    fieldsets = ((None, {"fields": ("title", "date", "send_date", "description")}),)
    #: available fields for searching
    search_fields = ("title", "description")
    #: field to use for date filtering
    date_hierarchy = "date"

    def change_view(self, request, object_id, form_url=""):
        """Render the change view.

        Disallow change access if a newsletter is marked as sent
        """
        obj = Newsletter.objects.filter(id=object_id)[0]
        if obj is not None and obj.sent is True:
            return redirect(obj)
        return super().change_view(request, object_id, form_url, {"newsletter": obj})

    def has_delete_permission(self, request, obj=None):
        """Check if delete permission is granted.

        Disallow deletion if a newsletter is marked as sent
        """
        if obj is not None and obj.sent is True:
            return False
        return super().has_delete_permission(request, obj=obj)

    def get_actions(self, request):
        """Remove the deletion action from the admin."""
        actions = super().get_actions(request)
        del actions["delete_selected"]
        return actions

    @object_action(
        label=_("Send"),
        permission="newsletters.send_newsletter",
        condition=lambda _, obj: not obj.sent,
        display_as_disabled_if_condition_not_met=True,
        log_message=_("Sent"),
        perform_after_saving=True,
    )
    def send(self, request, obj):
        """Reverse the review status."""
        services.send_newsletter(obj)
        return redirect("admin:newsletters_newsletter_changelist")

    @object_action(
        label=_("Show preview"),
        perform_after_saving=True,
        include_in_queryset_actions=False,
    )
    def preview(self, request, obj):
        """Reverse the review status."""
        return redirect("newsletters:preview", obj.pk)

    object_actions_after_related_objects = [
        "preview",
        "send",
    ]
