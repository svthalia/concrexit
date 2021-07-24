"""Partners app calendarjs API urls."""
from django.urls import path

from partners.api.calendarjs.views import CalendarJSPartnerEventListView

app_name = "partners"

urlpatterns = [
    path(
        "partners/",
        CalendarJSPartnerEventListView.as_view(),
        name="calendarjs-partners",
    ),
]
