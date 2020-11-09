"""
Thalia's root URL Configuration

The ``urlpatterns`` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/dev/topics/http/urls/

Examples:

* Function views

  1. Add an import: ``from my_app import views``
  2. Add a URL to ``urlpatterns``: ``path('', views.home, name='home')``

* Class-based views

  1. Add an import: ``from other_app.views import Home``
  2. Add a URL to urlpatterns: ``path('', Home.as_view(), name='home')``

* Including another URLconf

  1. Import the ``include()`` function::

        from django.conf.urls import url, include

  2. Add a URL to urlpatterns: ``path('blog/', include('blog.urls'))``
"""

import os.path

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from oauth2_provider.urls import base_urlpatterns
from oauth2_provider.views import AuthorizedTokensListView, AuthorizedTokenDeleteView
from rest_framework.schemas import get_schema_view

from activemembers.sitemaps import sitemap as activemembers_sitemap
from documents.sitemaps import sitemap as documents_sitemap
from education.sitemaps import sitemap as education_sitemap
from events.sitemaps import sitemap as events_sitemap
from members.sitemaps import sitemap as members_sitemap
from partners.sitemaps import sitemap as partners_sitemap
from singlepages.sitemaps import sitemap as singlepages_sitemap
from thabloid.sitemaps import sitemap as thabloid_sitemap
from thaliawebsite.forms import AuthenticationForm
from thaliawebsite.views import TestCrashView, IndexView
from utils.media.views import generate_thumbnail, private_media
from .api.openapi import OAuthSchemaGenerator
from .sitemaps import StaticViewSitemap

__all__ = ["urlpatterns"]

THALIA_SITEMAP = {
    "main-static": StaticViewSitemap,
}
THALIA_SITEMAP.update(activemembers_sitemap)
THALIA_SITEMAP.update(members_sitemap)
THALIA_SITEMAP.update(documents_sitemap)
THALIA_SITEMAP.update(thabloid_sitemap)
THALIA_SITEMAP.update(partners_sitemap)
THALIA_SITEMAP.update(education_sitemap)
THALIA_SITEMAP.update(events_sitemap)
THALIA_SITEMAP.update(singlepages_sitemap)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", IndexView.as_view(), name="index"),
    # Default helpers
    path(
        "user/",
        include(
            [
                path(
                    "oauth/",
                    include(
                        (
                            base_urlpatterns
                            + [
                                path(
                                    "authorised-apps/",
                                    AuthorizedTokensListView.as_view(),
                                    name="authorized-token-list",
                                ),
                                path(
                                    "authorised-apps/<int:pk>/delete/",
                                    AuthorizedTokenDeleteView.as_view(),
                                    name="authorized-token-delete",
                                ),
                            ],
                            "oauth2_provider",
                        ),
                        namespace="oauth2_provider",
                    ),
                ),
                path(
                    "login/",
                    LoginView.as_view(
                        authentication_form=AuthenticationForm,
                        redirect_authenticated_user=True,
                    ),
                    name="login",
                ),
                path("", include("django.contrib.auth.urls")),
            ]
        ),
    ),
    path(
        "i18n/",
        include(
            [
                path("", include("django.conf.urls.i18n")),
                path("js/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
            ]
        ),
    ),
    # Apps
    path("", include("singlepages.urls")),
    path("", include("merchandise.urls")),
    path("", include("thabloid.urls")),
    path("", include("registrations.urls")),
    path("", include("newsletters.urls")),
    path("", include("announcements.urls")),
    path("", include("pushnotifications.urls")),
    path("", include("photos.urls")),
    path("", include("members.urls")),
    path("", include("payments.urls")),
    path("", include("education.urls")),
    path("", include("activemembers.urls")),
    path("", include("documents.urls")),
    path("", include("events.urls")),
    path("", include("pizzas.urls")),
    path("", include("partners.urls")),
    path(
        "api/",
        include(
            [
                path("v1/", include("thaliawebsite.api.v1.urls")),
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
                path(
                    "docs",
                    TemplateView.as_view(
                        template_name="swagger.html",
                        extra_context={"schema_urls": ["schema-v1"]},
                    ),
                    name="swagger",
                ),
                path(
                    "docs/oauth2-redirect",
                    TemplateView.as_view(template_name="swagger-oauth2-redirect.html"),
                    name="swagger-oauth-redirect",
                ),
            ]
        ),
    ),
    # Sitemap
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": THALIA_SITEMAP},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Dependencies
    path(r"tinymce", include("tinymce.urls")),
    # Provide something to test error handling. Limited to admins.
    path("crash/", TestCrashView.as_view()),
    # Custom media paths
    re_path(
        r"^media/generate-thumbnail/(?P<request_path>.*)",
        generate_thumbnail,
        name="generate-thumbnail",
    ),
    re_path(
        r"^media/private/(?P<request_path>.*)$", private_media, name="private-media"
    ),
] + static(
    settings.MEDIA_URL + "public/",
    document_root=os.path.join(settings.MEDIA_ROOT, "public"),
)
