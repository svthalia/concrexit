"""The routes defined by this package."""
from django.urls import include, path

from announcements import views

#: the name of this app
app_name = "announcements"

#: the actual routes
urlpatterns = [
    path(
        "announcements/",
        include(
            [
                path(
                    "close-announcement",
                    views.close_announcement,
                    name="close-announcement",
                )
            ]
        ),
    )
]
