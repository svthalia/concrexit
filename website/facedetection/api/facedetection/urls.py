"""Events app calendarjs API urls."""
from django.urls import path

from .views import PhotoFaceEncodingView, ReferenceFaceEncodingView

app_name = "facedetection"

urlpatterns = [
    path(
        "reference/encoding/",
        ReferenceFaceEncodingView.as_view(),
        name="facedetection-reference-encoding",
    ),
    path(
        "photo/<int:pk>/encoding/",
        PhotoFaceEncodingView.as_view(),
        name="facedetection-photo-encoding",
    ),
]
