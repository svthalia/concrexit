from django.urls import path, include

from members.views import ObtainThaliaAuthToken

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("activemembers.api.v2.urls")),
]
