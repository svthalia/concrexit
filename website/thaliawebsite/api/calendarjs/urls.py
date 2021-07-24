from django.urls import path, include

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("events.api.calendarjs.urls")),
    path("", include("partners.api.calendarjs.urls")),
    path("", include("members.api.calendarjs.urls")),
]
