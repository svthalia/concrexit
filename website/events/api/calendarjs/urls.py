"""Events app calendarjs API urls."""
from django.urls import path

from events.api.calendarjs.views import (
    CalendarJSEventListView,
    CalendarJSUnpublishedEventListView,
)

app_name = "events"

urlpatterns = [
    path("events/", CalendarJSEventListView.as_view(), name="calendarjs-published",),
    path(
        "events/unpublished/",
        CalendarJSUnpublishedEventListView.as_view(),
        name="calendarjs-unpublished",
    ),
]
