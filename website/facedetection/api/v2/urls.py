"""Events app calendarjs API urls."""
from django.urls import path

from .views import ReferenceFaceDeleteView, ReferenceFaceListView, YourPhotosView

app_name = "facedetection"

urlpatterns = [
    path(
        "photos/facedetection/matches/",
        YourPhotosView.as_view(),
        name="your-photos",
    ),
    path(
        "photos/facedetection/reference-faces/",
        ReferenceFaceListView.as_view(),
        name="reference-faces",
    ),
    path(
        "photos/facedetection/reference-faces/<int:pk>/",
        ReferenceFaceDeleteView.as_view(),
        name="reference-faces-delete",
    ),
]
