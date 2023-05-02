from django.urls import include, path

from . import views

app_name = "facedetection"

urlpatterns = [
    path(
        "members/photos/facedetection/",
        include(
            [
                path("you/", views.your_photos, name="your-photos"),
                path(
                    "reference-faces/",
                    views.ReferenceFaceView.as_view(),
                    name="reference-faces",
                ),
                path(
                    "reference-faces/upload/",
                    views.ReferenceFaceUploadView.as_view(),
                    name="reference-faces-upload",
                ),
                path(
                    "reference-faces/delete/<int:pk>/",
                    views.ReferenceFaceDeleteView.as_view(),
                    name="reference-faces-delete",
                ),
            ]
        ),
    )
]
