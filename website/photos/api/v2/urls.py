"""Photos app API v2 urls."""
from django.urls import path, include

from photos.api.v2.views import (
    AlbumListView,
    AlbumDetailView,
    PhotoLikeView,
    UnprocessedFaceRecognitionView,
    FaceEncodingPostView,
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
                # path(
                #     "photos/<int:pk>/on-photo/", PersonOnPhotoView.as_view(),
                #     name="person-on-photo"
                # ),
                path(
                    "face-recognition/unprocessed/",
                    UnprocessedFaceRecognitionView.as_view(),
                    name="face-recognition-unprocessed",
                ),
                path(
                    "face-recognition/<str:type>/<int:pk>/",
                    FaceEncodingPostView.as_view(),
                    name="face-encoding-post",
                ),
            ]
        ),
    ),
]
