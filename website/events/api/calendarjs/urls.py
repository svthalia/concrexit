"""Events app calendarjs API urls."""
from django.urls import path

from events.api.calendarjs.views import (
    CalendarJSEventListView,
    CalendarJSUnpublishedEventListView,
    CalendarJSExternalEventListView,
    CalendarJSUnpublishedExternalEventListView,
)

app_name = "events"

urlpatterns = [
    path(
        "events/",
        CalendarJSEventListView.as_view(),
        name="calendarjs-published",
    ),
    path(
        "external/",
        CalendarJSExternalEventListView.as_view(),
        name="calendarjs-external",
    ),
    path(
        "events/unpublished/",
        CalendarJSUnpublishedEventListView.as_view(),
        name="calendarjs-unpublished",
    ),
    path(
        "external/unpublished/",
        CalendarJSUnpublishedExternalEventListView.as_view(),
        name="calendarjs-external-unpublished",
    ),

]
