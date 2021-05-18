"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.admin.views import (
    EventAdminListAPIView,
    EventAdminDetailAPIView,
    EventRegistrationAdminFieldsView,
    EventRegistrationAdminDetailView,
    EventRegistrationsAdminListView,
)

urlpatterns = [
    path("events/", EventAdminListAPIView.as_view(), name="events-list"),
    path("events/<int:pk>/", EventAdminDetailAPIView.as_view(), name="event-detail",),
    path(
        "events/<int:pk>/registrations/",
        EventRegistrationsAdminListView.as_view(),
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
