"""Activemembers app API v2 urls."""
from django.urls import include, path

from activemembers.api.v2.views import MemberGroupDetailView, MemberGroupListView

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
            ]
        ),
    ),
]
