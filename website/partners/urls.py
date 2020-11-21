from django.urls import path, include

from . import views
from .api.calendarjs.views import CalendarJSPartnerEventListView

app_name = "partners"

urlpatterns = [
    path(
        "career/",
        include(
            [
                path("", views.index, name="index"),
                path("partners/<slug>/", views.partner, name="partner"),
                path("vacancies", views.vacancies, name="vacancies"),
            ]
        ),
    ),
    path(
        "api/calendarjs/",
        include(
            [
                path(
                    "partners/",
                    CalendarJSPartnerEventListView.as_view(),
                    name="calendarjs-partners",
                ),
            ]
        ),
    ),
]
