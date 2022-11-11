"""Photos app API v2 urls."""
from django.urls import path

from facerecognition.api.v2.views import (
    FaceEncodingPostView,
    UnprocessedFaceRecognitionView,
)

app_name = "photos"

urlpatterns = [
    path(
        "unprocessed/",
        UnprocessedFaceRecognitionView.as_view(),
        name="unprocessed",
    ),
    path(
        "encodings/<str:type>/<int:pk>/",
        FaceEncodingPostView.as_view(),
        name="encoding-callback",
    ),
]
