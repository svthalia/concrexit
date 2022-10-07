"""The routes defined by the thabloid package."""
from django.urls import include, path

from . import views

app_name = "thabloid"

urlpatterns = [
    path(
        "members/",
        include(
            [
                path(
                    "thabloid/",
                    include(
                        [
                            path("", views.index, name="index"),
                            path(
                                "pages/<int:year>/<int:issue>/",
                                views.pages,
                                name="pages",
                            ),
                        ]
                    ),
                )
            ]
        ),
    )
]
