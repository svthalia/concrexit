from django.contrib import admin
from django.template.defaultfilters import striptags

from thaliawebsite.templatetags.bleach_tags import bleach
from utils.translation import TranslatedModelAdmin

from .models import Announcement, FrontpageArticle


@admin.register(Announcement)
class AnnouncementAdmin(TranslatedModelAdmin):
    list_display = ('content_html', 'since', 'until', 'visible')

    def content_html(self, obj):
        # Both bleach and striptags.
        # First to convert HTML entities and second to strip all HTML
        return bleach(striptags(obj.content))

    def visible(self, obj):
        return obj.is_visible
    visible.boolean = True


@admin.register(FrontpageArticle)
class FrontpageArticleAdmin(TranslatedModelAdmin):
    list_display = ('title', 'since', 'until', 'visible')

    def visible(self, obj):
        return obj.is_visible
    visible.boolean = True
