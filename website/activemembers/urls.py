"""The routes defined by the activemembers package."""
from django.urls import include, path, re_path

from activemembers.views import (
    BoardDetailView,
    BoardIndexView,
    CommitteeDetailView,
    CommitteeIndexView,
    SocietyDetailView,
    SocietyIndexView,
)

app_name = "activemembers"

urlpatterns = [
    path(
        "association/",
        include(
            [
                path(
                    "committees/<int:pk>/",
                    CommitteeDetailView.as_view(),
                    name="committee",
                ),
                path("committees/", CommitteeIndexView.as_view(), name="committees"),
                path(
                    "societies/<int:pk>/", SocietyDetailView.as_view(), name="society"
                ),
                path("societies/", SocietyIndexView.as_view(), name="societies"),
                re_path(
                    r"boards/(?P<since>\d{4})-(?P<until>\d{4})/$",
                    BoardDetailView.as_view(),
                    name="board",
                ),
                path("boards/", BoardIndexView.as_view(), name="boards"),
            ]
        ),
    ),
]
