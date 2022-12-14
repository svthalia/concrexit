"""Photos app API v2 urls."""
from django.urls import include, path

from photos.api.v2.views import (
    AlbumDetailView,
    AlbumListView,
    LikedPhotosListView,
    PhotoLikeView,
)

app_name = "photos"

urlpatterns = [
    path(
        "photos/",
        include(
            [
                path("albums/", AlbumListView.as_view(), name="album-list"),
                path(
                    "albums/<slug:slug>/",
                    AlbumDetailView.as_view(),
                    name="album-detail",
                ),
                path(
                    "photos/<int:pk>/like/", PhotoLikeView.as_view(), name="photo-like"
                ),
                path(
                    "liked-photos/", LikedPhotosListView.as_view(), name="liked-photos"
                ),
            ]
        ),
    ),
]
