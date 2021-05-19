"""Concrexit API url schemes."""
from django.conf import settings
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view

from thaliawebsite.api.openapi import OAuthSchemaGenerator

app_name = "api"

urlpatterns = [
    path(
        "",
        include(
            [
                path("v1/", include("thaliawebsite.api.v1.urls", namespace="v1")),
                path(
                    "v1/schema",
                    get_schema_view(
                        title="API v1",
                        version=settings.SOURCE_COMMIT,
                        url="/api/v1/",
                        urlconf="thaliawebsite.api.v1.urls",
                        generator_class=OAuthSchemaGenerator,
                    ),
                    name="schema-v1",
                ),
                path("v2/", include("thaliawebsite.api.v2.urls", namespace="v2")),
                path(
                    "v2/schema",
                    get_schema_view(
                        title="API v2",
                        version=settings.SOURCE_COMMIT,
                        url="/api/v2/",
                        urlconf="thaliawebsite.api.v2.urls",
                        generator_class=OAuthSchemaGenerator,
                        public=True,
                    ),
                    name="schema-v2",
                ),
                path(
                    "docs",
                    TemplateView.as_view(
                        template_name="swagger/index.html",
                        extra_context={
                            "schema_urls": ["api:schema-v1", "api:schema-v2"]
                        },
                    ),
                    name="swagger",
                ),
                path(
                    "docs/oauth2-redirect",
                    TemplateView.as_view(template_name="swagger/oauth2-redirect.html"),
                    name="swagger-oauth-redirect",
                ),
            ]
        ),
    )
]
