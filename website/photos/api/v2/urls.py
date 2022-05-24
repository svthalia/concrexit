"""Photos app API v2 urls."""
from django.urls import path, include

from photos.api.v2.views import AlbumListView, AlbumDetailView, PhotoKudoView

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
                    "photos/<int:pk>/kudos/", PhotoKudoView.as_view(), name="photo-kudo"
                ),
            ]
        ),
    ),
]
