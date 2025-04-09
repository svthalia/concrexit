from announcements import views
from django.urls import include, path

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
                    views.close_announcement_view,
                    name="close-announcement",
                )
            ]
        ),
    )
]
