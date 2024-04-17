"""Concrexit API url schemes."""
from django.urls import include, path
from django.views.generic import TemplateView

app_name = "api"

urlpatterns = [
    path(
        "",
        include(
            [
                path("v2/", include("thaliawebsite.api.v2.urls", namespace="v2")),
                path(
                    "calendarjs/",
                    include(
                        "thaliawebsite.api.calendarjs.urls", namespace="calendarjs"
                    ),
                ),
                path(
                    "facedetection/",
                    include(
                        "thaliawebsite.api.facedetection.urls",
                        namespace="facedetection",
                    ),
                ),
                path(
                    "docs",
                    TemplateView.as_view(
                        template_name="swagger/index.html",
                        extra_context={
                            "schema_urls": ["api:v2:schema", "api:v1:schema"]
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
