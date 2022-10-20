"""Announcements app API v2 urls."""
from django.urls import include, path

from announcements.api.v2.views import (
    FrontpageArticleDetailView,
    FrontpageArticleListView,
    SlideDetailView,
    SlideListView,
)

app_name = "announcements"

urlpatterns = [
    path(
        "announcements/",
        include(
            [
                path("slides/", SlideListView.as_view(), name="slide-list"),
                path(
                    "slides/<int:pk>/",
                    SlideDetailView.as_view(),
                    name="slide-detail",
                ),
                path(
                    "frontpage-articles/",
                    FrontpageArticleListView.as_view(),
                    name="frontpage-list",
                ),
                path(
                    "frontpage-articles/<int:pk>/",
                    FrontpageArticleDetailView.as_view(),
                    name="frontpage-detail",
                ),
            ]
        ),
    ),
]
