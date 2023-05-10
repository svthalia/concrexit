"""Events app calendarjs API urls."""
from django.urls import path

from .views import FaceEncodingPostView

app_name = "facedetection"

urlpatterns = [
    path(
        "encodings/<str:type>/<int:pk>/",
        FaceEncodingPostView.as_view(),
        name="encoding-callback",
    ),
]
