from django.conf import settings
from django.urls import path, include
from rest_framework.schemas import get_schema_view

from thaliawebsite.api.openapi import OAuthSchemaGenerator

app_name = "thaliawebsite"

urlpatterns = [
    path("admin/", include("thaliawebsite.api.v2.admin.urls", namespace="admin")),
    path("", include("activemembers.api.v2.urls", namespace="activemembers")),
    path("", include("announcements.api.v2.urls")),
    path("", include("events.api.v2.urls")),
    path("", include("members.api.v2.urls")),
    path("", include("partners.api.v2.urls")),
    path("", include("payments.api.v2.urls")),
    path("", include("photos.api.v2.urls")),
    path("", include("pizzas.api.v2.urls")),
    path("", include("pushnotifications.api.v2.urls")),
    path(
        "schema",
        get_schema_view(
            title="API v2",
            version=settings.SOURCE_COMMIT,
            url="/api/v2/",
            urlconf="thaliawebsite.api.v2.urls",
            generator_class=OAuthSchemaGenerator,
            public=True,
        ),
        name="schema",
    ),
]
