from django.urls import path, include

from members.views import ObtainThaliaAuthToken


app_name = "thaliawebsite"

urlpatterns = [
    path("token-auth/", ObtainThaliaAuthToken.as_view()),
    path("", include("activemembers.api.v1.urls")),
    path("", include("announcements.api.v1.urls")),
    path("", include("events.api.v1.urls")),
    path("", include("members.api.v1.urls")),
    path("", include("partners.api.v1.urls")),
    path("", include("pizzas.api.v1.urls")),
    path("", include("photos.api.v1.urls")),
    path("", include("pushnotifications.api.v1.urls")),
    path("", include("payments.api.v1.urls")),
]
