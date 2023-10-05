from django.conf import settings
from django.urls import include, path

from rest_framework.schemas import get_schema_view

from thaliawebsite.api.openapi import OAuthSchemaGenerator

app_name = "thaliawebsite"

urlpatterns = [
    path("", include("activemembers.api.v1.urls")),
    path("", include("announcements.api.v1.urls")),
    path("", include("events.api.v1.urls")),
    path("", include("members.api.v1.urls")),
    path("", include("partners.api.v1.urls")),
    path("", include("pizzas.api.v1.urls")),
    path("", include("photos.api.v1.urls")),
    path("", include("pushnotifications.api.v1.urls")),
    path("", include("payments.api.v1.urls")),
    path(
        "schema",
        get_schema_view(
            title="API v1",
            version=settings.SOURCE_COMMIT,
            url="/api/v1/",
            urlconf="thaliawebsite.api.v1.urls",
            generator_class=OAuthSchemaGenerator,
        ),
        name="schema",
    ),
]
