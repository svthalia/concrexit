"""Thabloid API v2 urls."""
from django.urls import include, path

from thabloid.api.v2.views import ThabloidDetailView, ThabloidListView

app_name = "thabloid"

urlpatterns = [
    path(
        "thabloid/",
        include(
            [
                path("thabloids/", ThabloidListView.as_view(), name="thabloid-list"),
                path(
                    "thabloids/<int:pk>",
                    ThabloidDetailView.as_view(),
                    name="thabloid-detail",
                ),
            ]
        ),
    ),
]
