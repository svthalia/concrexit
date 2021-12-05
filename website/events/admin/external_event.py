from django.contrib import admin

from events.admin.filters import LectureYearFilter
from events.models.external_event import ExternalEvent


@admin.register(ExternalEvent)
class ExternalEventAdmin(admin.ModelAdmin):
    """Class to show external events in the admin."""

    fields = (
        "organiser",
        "title",
        "category",
        "description",
        "location",
        "start",
        "end",
        "url",
        "published",
    )
    list_display = ("title", "start", "end", "organiser", "published")
    list_filter = (LectureYearFilter, "start", "category", "published")
    date_hierarchy = "start"
    search_fields = ("title", "organiser")
