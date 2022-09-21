from django.urls import path, include

from . import views

app_name = "photos"

urlpatterns = [
    path(
        "members/photos/",
        include(
            [
                path("", views.index, name="index"),
                path("liked", views.liked_photos, name="liked-photos"),
                path(
                    "<slug>/",
                    include(
                        [
                            path("", views.detail, name="album"),
                            path(
                                "download/",
                                include(
                                    [
                                        path(
                                            "<filename>",
                                            views.download,
                                            name="download",
                                        ),
                                        path(
                                            "<token>/",
                                            include(
                                                [
                                                    path(
                                                        "<filename>",
                                                        views.shared_download,
                                                        name="shared-download",
                                                    ),
                                                ]
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            path("<token>/", views.shared_album, name="shared-album"),
                        ]
                    ),
                ),
            ]
        ),
    )
]
