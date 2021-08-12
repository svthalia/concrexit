"""Registers admin interfaces for the newsletters module."""
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.shortcuts import redirect

from newsletters.models import Newsletter, NewsletterEvent, NewsletterItem
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
class NewsletterAdmin(ModelAdmin):
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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Render the change view.

        Disallow change access if a newsletter is marked as sent
        """
        obj = Newsletter.objects.filter(id=object_id)[0]
        if obj is not None and obj.sent is True:
            return redirect(obj)
        return super().change_view(request, object_id, form_url, extra_context)

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
