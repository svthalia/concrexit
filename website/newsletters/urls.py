"""The routes defined by the newsletters package."""
from django.urls import path, include

from . import views

app_name = "newsletters"

urlpatterns = [
    path(
        "newsletters/",
        include(
            [
                path("<int:pk>/", views.preview, name="preview"),
                path("<int:pk>/<str:lang>/", views.preview, name="preview-localised"),
            ]
        ),
    )
]
