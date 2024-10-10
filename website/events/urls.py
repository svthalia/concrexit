"""Routes defined by the events package."""
from django.urls import include, path
from django.views.generic import TemplateView

from events.feeds import EventFeed
from events.views import (
    AlumniEventsView,
    EventCancelView,
    EventDetail,
    EventIndex,
    EventRegisterView,
    MarkPresentView,
    NextEventView,
    RegistrationView,
)

app_name = "events"

urlpatterns = [
    path(
        "events/",
        include(
            [
                path("<int:pk>/", EventDetail.as_view(), name="event"),
                path("next/", NextEventView.as_view(), name="next"),
                path(
                    "sync/",
                    TemplateView.as_view(template_name="events/synchronize.html"),
                    name="synchronize",
                ),
                path("<slug:slug>/", EventDetail.as_view(), name="event"),
                path(
                    "<int:pk>/registration/register/",
                    EventRegisterView.as_view(),
                    name="register",
                ),
                path(
                    "<int:pk>/registration/cancel/",
                    EventCancelView.as_view(),
                    name="cancel",
                ),
                path(
                    "<int:pk>/mark-present/<uuid:token>/",
                    MarkPresentView.as_view(),
                    name="mark-present",
                ),
                path(
                    "<int:pk>/registration/",
                    RegistrationView.as_view(),
                    name="registration",
                ),
                path("", EventIndex.as_view(), name="index"),
                path("ical/nl.ics", EventFeed(), name="ical-nl"),
                path("ical/en.ics", EventFeed(), name="ical-en"),
            ]
        ),
    ),
    path("association/alumni/", AlumniEventsView.as_view(), name="alumni"),
]
