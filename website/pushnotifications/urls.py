"""The routes defined by the pushnotifications package."""
from django.urls import include, path

from . import views

app_name = "pushnotifications"

urlpatterns = [
    path(
        "pushnotifications/",
        include(
            [
                path("admin/send/<int:pk>/", views.admin_send, name="admin-send"),
            ]
        ),
    )
]
