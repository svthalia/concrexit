"""Activemembers app API v2 urls."""
from django.urls import include, path, re_path

from activemembers.api.v2.views import (
    BoardDetailView,
    MemberGroupDetailView,
    MemberGroupListView,
)

app_name = "activemembers"

urlpatterns = [
    path(
        "activemembers/",
        include(
            [
                path("groups/", MemberGroupListView.as_view(), name="group-list"),
                path(
                    "groups/<int:pk>/",
                    MemberGroupDetailView.as_view(),
                    name="group-detail",
                ),
                re_path(
                    r"boards/(?P<since>\d{4})-(?P<until>\d{4})/$",
                    BoardDetailView.as_view(),
                    name="board-detail",
                ),
            ]
        ),
    ),
]
