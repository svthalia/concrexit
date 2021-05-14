"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.admin.views import EventAdminListAPIView, EventAdminDetailAPIView

urlpatterns = [
    path("events/", EventAdminListAPIView.as_view(), name="events-list"),
    path("events/<int:pk>/", EventAdminDetailAPIView.as_view(), name="event-detail",),
]
