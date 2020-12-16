"""Activemembers app API v2 urls."""
from django.urls import path, include

from activemembers.api.v2.views import (
    CommitteeDetailView,
    CommitteeListView,
    SocietyDetailView,
    SocietyListView,
    BoardDetailView,
    BoardListView,
    MemberGroupListView,
    MemberGroupDetailView,
)

urlpatterns = [
    path(
        "activemembers/",
        include(
            [
                path("committees/", CommitteeListView.as_view(), name="committee-list"),
                path(
                    "committees/<int:pk>/",
                    CommitteeDetailView.as_view(),
                    name="committee-detail",
                ),
                path("societies/", SocietyListView.as_view(), name="society-list"),
                path(
                    "societies/<int:pk>/",
                    SocietyDetailView.as_view(),
                    name="society-detail",
                ),
                path("boards/", BoardListView.as_view(), name="board-list"),
                path(
                    "boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"
                ),
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
