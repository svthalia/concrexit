"""The routes defined by the thabloid package."""
from django.urls import include, path

from . import views

app_name = "wrapped"

urlpatterns = [
    path(
        "user/",
        include(
            [
                path(
                    "wrapped/",
                    include(
                        [
                            path(
                                "",
                                views.index,
                                name="index",
                            ),
                        ]
                    ),
                )
            ]
        ),
    )
]
