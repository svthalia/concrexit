"""The routes defined by the documents package."""
from django.urls import include, path

from . import views

app_name = "documents"

urlpatterns = [
    path(
        "association/documents/",
        include(
            [
                path(
                    "document/<int:pk>/",
                    views.DocumentDownloadView.as_view(),
                    name="document",
                ),
                path("", views.DocumentsIndexView.as_view(), name="index"),
            ]
        ),
    )
]
