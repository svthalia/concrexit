"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.views import (
    EventListView,
    EventDetailView,
    EventRegistrationsView,
    EventRegistrationDetailView,
    EventRegistrationFieldsView,
)

urlpatterns = [
    path("events/", EventListView.as_view(), name="events-list"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event-detail",),
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
]
