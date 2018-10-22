"""Registers admin interfaces for the announcements module"""
from django.contrib import admin
from django.template.defaultfilters import striptags

from thaliawebsite.templatetags.bleach_tags import bleach
from utils.translation import TranslatedModelAdmin

from .models import Announcement, FrontpageArticle, Slide


@admin.register(Announcement)
class AnnouncementAdmin(TranslatedModelAdmin):
    """Manage the admin pages for the announcements"""

    #: show these fields in the admin overview list
    #: see :py:method:content_html for the 'content_html' field
    #: see :py:method:visible for the visible field
    list_display = ('content_html', 'since', 'until', 'visible')

    def content_html(self, obj):  # pylint: disable=no-self-use
        """Get the content of the object as html

        :param obj: the object to render for
        :return: the stripped html
        """
        # Both bleach and striptags.
        # First to convert HTML entities and second to strip all HTML
        return bleach(striptags(obj.content))

    def visible(self, obj):  # pylint: disable=no-self-use
        """Is the object visible"""
        return obj.is_visible
    visible.boolean = True


@admin.register(FrontpageArticle)
class FrontpageArticleAdmin(TranslatedModelAdmin):
    """Manage front page articles"""

    #: available fields in the admin overview list
    list_display = ('title', 'since', 'until', 'visible')

    def visible(self, obj):  # pylint: disable=no-self-use
        """Is the object visible"""
        return obj.is_visible
    visible.boolean = True


@admin.register(Slide)
class SlideAdmin(TranslatedModelAdmin):
    """Manage the admin pages for the slides"""

    #: show these fields in the admin overview list
    #: see :py:method:visible for the visible field
    list_display = ('title', 'since', 'until', 'visible')

    def visible(self, obj):  # pylint: disable=no-self-use
        """Is the object visible"""
        return obj.is_visible
    visible.boolean = True
