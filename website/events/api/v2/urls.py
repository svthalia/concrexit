"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.views import (
    EventDetailView,
    EventListView,
    EventRegistrationDetailView,
    EventRegistrationFieldsView,
    EventRegistrationsView,
    ExternalEventDetailView,
    ExternalEventListView,
)

app_name = "events"

urlpatterns = [
    path("events/", EventListView.as_view(), name="events-list"),
    path(
        "events/<int:pk>/",
        EventDetailView.as_view(),
        name="event-detail",
    ),
    path(
        "events/<int:pk>/registrations/",
        EventRegistrationsView.as_view(),
        name="event-registrations",
    ),
    path(
        "events/<int:event_id>/registrations/<int:pk>/",
        EventRegistrationDetailView.as_view(),
        name="event-registration-detail",
    ),
    path(
        "events/<int:event_id>/registrations/<int:registration_id>/fields/",
        EventRegistrationFieldsView.as_view(),
        name="event-registration-fields",
    ),
    path(
        "events/external/", ExternalEventListView.as_view(), name="external-events-list"
    ),
    path(
        "events/external/<int:pk>/",
        ExternalEventDetailView.as_view(),
        name="external-event-detail",
    ),
]
