from django.urls import path, include

from members.views import ObtainThaliaAuthToken


app_name = "thaliawebsite"

urlpatterns = [
    path("token-auth/", ObtainThaliaAuthToken.as_view()),
    path("", include("activemembers.api.v1.urls")),
    path("", include("announcements.api.v1.urls")),
    path("", include("events.api.urls")),
    path("", include("members.api.urls")),
    path("", include("partners.api.urls")),
    path("", include("pizzas.api.urls")),
    path("", include("photos.api.urls")),
    path("", include("pushnotifications.api.urls")),
]
