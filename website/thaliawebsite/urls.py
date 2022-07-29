"""Thalia's root URL Configuration.

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

import debug_toolbar
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path
from django.views.i18n import JavaScriptCatalog
from oauth2_provider.urls import base_urlpatterns
from oauth2_provider.views import (
    AuthorizedTokensListView,
    AuthorizedTokenDeleteView,
    ConnectDiscoveryInfoView,
    JwksInfoView,
    UserInfoView,
)

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
from utils.media.views import get_thumbnail, private_media
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
        "",
        include(
            (
                [
                    path(
                        "user/oauth/",
                        include(
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
                                path(
                                    "keys/",
                                    JwksInfoView.as_view(),
                                    name="jwks-info",
                                ),
                                path(
                                    "info/",
                                    UserInfoView.as_view(),
                                    name="user-info",
                                ),
                            ]
                        ),
                    ),
                    path(
                        ".well-known/openid-configuration/",
                        ConnectDiscoveryInfoView.as_view(),
                        name="oidc-connect-discovery-info",
                    ),
                ],
                "oauth2_provider",
            ),
            namespace="oauth2_provider",
        ),
    ),
    path(
        "user/",
        include(
            [
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
    path("", include("sales.urls")),
    path("api/", include("thaliawebsite.api.urls")),
    # Sitemap
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": THALIA_SITEMAP},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Dependencies
    path("tinymce/", include("tinymce.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    # Provide something to test error handling. Limited to admins.
    path("crash/", TestCrashView.as_view()),
    # Custom media paths
    re_path(
        r"^media/thumbnail/(?P<request_path>.*)",
        get_thumbnail,
        name="get-thumbnail",
    ),
    re_path(
        r"^media/private/(?P<request_path>.*)$", private_media, name="private-media"
    ),
    path("", include("shortlinks.urls")),
] + static(
    settings.PUBLIC_MEDIA_URL,
    document_root=os.path.join(settings.MEDIA_ROOT, settings.PUBLIC_MEDIA_LOCATION),
)
