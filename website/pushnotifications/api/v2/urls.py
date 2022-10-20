"""Pushnotifications app API v2 urls."""
from django.urls import include, path

from pushnotifications.api.v2.views import (
    CategoryListView,
    DeviceDetailView,
    DeviceListView,
    MessageDetailView,
    MessageListView,
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
                path(
                    "devices/",
                    DeviceListView.as_view(),
                    name="device-list",
                ),
                path(
                    "devices/<int:pk>/",
                    DeviceDetailView.as_view(),
                    name="device-detail",
                ),
                path(
                    "categories/",
                    CategoryListView.as_view(),
                    name="category-list",
                ),
            ]
        ),
    ),
]
