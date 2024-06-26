"""The routes defined by the newsletters package."""

from django.urls import include, path

from . import views

app_name = "newsletters"

urlpatterns = [
    path(
        "newsletters/",
        include(
            [
                path("<int:pk>/", views.preview, name="preview"),
            ]
        ),
    )
]
