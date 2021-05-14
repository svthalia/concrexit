from django.urls import path, include

from thaliawebsite.api.v2 import admin

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("events.api.v2.admin.urls")),
]
