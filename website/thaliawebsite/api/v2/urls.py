from django.urls import path, include

from thaliawebsite.api.v2 import admin

app_name = "thaliawebsite"

urlpatterns = [
    path("admin/", include("thaliawebsite.api.v2.admin.urls")),
    path("", include("activemembers.api.v2.urls")),
    path("", include("announcements.api.v2.urls")),
    path("", include("events.api.v2.urls")),
    path("", include("members.api.v2.urls")),
    path("", include("partners.api.v2.urls")),
    path("", include("payments.api.v2.urls")),
    path("", include("photos.api.v2.urls")),
    path("", include("pizzas.api.v2.urls")),
    path("", include("pushnotifications.api.v2.urls")),
    path("", include("sales.api.v2.urls")),
]
