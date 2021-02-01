"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.views import (
    EventListView,
    EventDetailView,
    EventRegistrationListView,
)

urlpatterns = [
    path("events/", EventListView.as_view(), name="event-list"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event-detail",),
    path(
        "events/<int:pk>/registrations",
        EventRegistrationListView.as_view(),
        name="event-registrations",
    ),
]
