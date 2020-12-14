from django.urls import path, include

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("activemembers.api.v2.urls")),
    path("", include("announcements.api.v2.urls")),
    path("", include("events.api.v2.urls")),
    path("", include("members.api.v2.urls")),
    path("", include("partners.api.v2.urls")),
    path("", include("payments.api.v2.urls")),
    path("", include("photos.api.v2.urls")),
    path("", include("pizzas.api.v2.urls")),
    path("", include("pushnotifications.api.v2.urls")),
]
