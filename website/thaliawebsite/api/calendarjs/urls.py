from django.urls import include, path

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("events.api.calendarjs.urls")),
    path("", include("members.api.calendarjs.urls")),
]
