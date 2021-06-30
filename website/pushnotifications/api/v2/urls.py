"""Pushnotifications app API v2 urls."""
from django.urls import path, include

from pushnotifications.api.v2.views import (
    DeviceDetailView,
    DeviceListView,
    MessageDetailView,
    MessageListView,
    CategoryListView,
)

app_name = "pushnotifications"

urlpatterns = [
    path(
        "pushnotifications/",
        include(
            [
                path("messages/", MessageListView.as_view(), name="device-list"),
                path(
                    "messages/<int:pk>/",
                    MessageDetailView.as_view(),
                    name="device-detail",
                ),
                path("devices/", DeviceListView.as_view(), name="device-list",),
                path(
                    "devices/<int:pk>/",
                    DeviceDetailView.as_view(),
                    name="device-detail",
                ),
                path("categories/", CategoryListView.as_view(), name="category-list",),
            ]
        ),
    ),
]
