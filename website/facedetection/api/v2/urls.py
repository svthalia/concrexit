"""Events app calendarjs API urls."""
from django.urls import path

from .views import ReferenceFaceDeleteView, ReferenceFaceListView

app_name = "facedetection"

urlpatterns = [
    # path(
    #     "photos/facedetection/matches/",
    #     FaceDetectionListView.as_view(),
    #     name="matches",
    # ),
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
