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
                path("v2/", include("thaliawebsite.api.v2.urls", namespace="v2")),
                path(
                    "calendarjs/",
                    include(
                        "thaliawebsite.api.calendarjs.urls", namespace="calendarjs"
                    ),
                ),
                path(
                    "docs",
                    TemplateView.as_view(
                        template_name="swagger/index.html",
                        extra_context={
                            "schema_urls": ["api:v1:schema", "api:v2:schema"]
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
