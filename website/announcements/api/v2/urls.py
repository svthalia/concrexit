from announcements.api.v2.views import (
    AnnouncementDetailView,
    AnnouncementListView,
    FrontpageArticleDetailView,
    FrontpageArticleListView,
    SlideDetailView,
    SlideListView,
)
from django.urls import include, path

app_name = "announcements"

urlpatterns = [
    path(
        "announcements/",
        include(
            [
                path(
                    "announcements/",
                    AnnouncementListView.as_view(actions={"get": "list"}),
                    name="announcement-list",
                ),
                path(
                    "announcements/<int:pk>/",
                    AnnouncementDetailView.as_view(actions={"delete": "hide"}),
                    name="announcement-detail",
                ),
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
