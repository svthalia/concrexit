"""Partners app calendarjs API urls."""
from django.urls import path

from members.api.calendarjs.views import CalendarJSBirthdayListView

app_name = "members"

urlpatterns = [
    path(
        "birthdays/",
        CalendarJSBirthdayListView.as_view(),
        name="calendarjs-birthdays",
    ),
]
