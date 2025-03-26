from django.urls import include, path, re_path

from . import views

app_name = "photos"

urlpatterns = [
    path(
        "members/photos/",
        include(
            [
                path("", views.IndexView.as_view(), name="index"),
                re_path("(?P<year>([0-9]{4}|older))/$", views.IndexView.as_view(), name="index-filter"),
                path("liked/", views.LikedPhotoView.as_view(), name="liked-photos"),
                path(
                    "<slug>/",
                    include(
                        [
                            path("", views.AlbumDetailView.as_view(), name="album"),
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
                            path(
                                "<token>/",
                                views.SharedAlbumView.as_view(),
                                name="shared-album",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    )
]
