"""Registers admin interfaces for the announcements module."""
from django.contrib import admin
from django.template.defaultfilters import striptags

from events.admin.event import EventAdmin as BaseEventAdmin
from events.models import Event
from thaliawebsite.templatetags.bleach_tags import bleach

from .models import Announcement, FrontpageArticle, Slide


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Manage the admin pages for the announcements."""

    #: show these fields in the admin overview list
    #: see :py:method:content_html for the 'content_html' field
    #: see :py:method:visible for the visible field
    list_display = ("content_html", "since", "until", "visible")

    def content_html(self, obj):
        """Get the content of the object as html.

        :param obj: the object to render for
        :return: the stripped html
        """
        # Both bleach and striptags.
        # First to convert HTML entities and second to strip all HTML
        return bleach(striptags(obj.content))

    def visible(self, obj):
        """Is the object visible."""
        return obj.is_visible

    visible.boolean = True


@admin.register(FrontpageArticle)
class FrontpageArticleAdmin(admin.ModelAdmin):
    """Manage front page articles."""

    #: available fields in the admin overview list
    list_display = ("title", "since", "until", "visible")

    def visible(self, obj):
        """Is the object visible."""
        return obj.is_visible

    visible.boolean = True


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    """Manage the admin pages for the slides."""

    #: show these fields in the admin overview list
    #: see :py:method:visible for the visible field
    list_display = ("title", "since", "until", "visible")

    def visible(self, obj):
        """Is the object visible."""
        return obj.is_visible

    visible.boolean = True


class SlideInline(admin.StackedInline):
    model = Slide
    extra = 0
    classes = ("collapse",)


class EventAdmin(BaseEventAdmin):
    def get_inlines(self, request, obj=None):
        return [*super().get_inlines(request, obj), SlideInline]


# Unregister the original EventAdmin and register the new one with SlideInline.
admin.site.unregister(Event)
admin.site.register(Event, EventAdmin)
