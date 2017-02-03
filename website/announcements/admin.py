from django.contrib import admin

from utils.translation import TranslatedModelAdmin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(TranslatedModelAdmin):
    list_display = ('content', 'since', 'until', 'visible')

    def visible(self, obj):
        return obj.is_visible
    visible.boolean = True
