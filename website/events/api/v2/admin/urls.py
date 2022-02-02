"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.admin.views import (
    EventAdminListCreateAPIView,
    EventAdminDetailAPIView,
    EventRegistrationAdminFieldsView,
    EventRegistrationAdminDetailView,
    EventRegistrationAdminListView,
)

app_name = "events"

urlpatterns = [
    path("events/", EventAdminListCreateAPIView.as_view(), name="events-index"),
    path(
        "events/<int:pk>/",
        EventAdminDetailAPIView.as_view(),
        name="event-detail",
    ),
    path(
        "events/<int:pk>/registrations/",
        EventRegistrationAdminListView.as_view(),
        name="event-registrations",
    ),
    path(
        "events/<int:event_id>/registrations/<int:pk>/",
        EventRegistrationAdminDetailView.as_view(),
        name="event-registration-detail",
    ),
    path(
        "events/<int:event_id>/registrations/<int:registration_id>/fields/",
        EventRegistrationAdminFieldsView.as_view(),
        name="event-registration-fields",
    ),
]
