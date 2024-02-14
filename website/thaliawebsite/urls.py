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

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path
from django.views.i18n import JavaScriptCatalog

import debug_toolbar
from oauth2_provider.urls import base_urlpatterns
from oauth2_provider.views import (
    AuthorizedTokenDeleteView,
    AuthorizedTokensListView,
    ConnectDiscoveryInfoView,
    JwksInfoView,
    UserInfoView,
)
from two_factor.urls import urlpatterns as tf_urls

from activemembers.sitemaps import sitemap as activemembers_sitemap
from documents.sitemaps import sitemap as documents_sitemap
from education.sitemaps import sitemap as education_sitemap
from events.sitemaps import sitemap as events_sitemap
from members.sitemaps import sitemap as members_sitemap
from partners.sitemaps import sitemap as partners_sitemap
from singlepages.sitemaps import sitemap as singlepages_sitemap
from thabloid.sitemaps import sitemap as thabloid_sitemap
from thaliawebsite.views import (
    IndexView,
    LogoutView,
    RateLimitedLoginView,
    RateLimitedPasswordResetView,
    TestCrashView,
    admin_unauthorized_view,
)
from utils.media.views import private_media

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
    path(
        "admin/login/",
        admin_unauthorized_view,
        name="login-redirect",
    ),
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
                    "password_change/",
                    auth_views.PasswordChangeView.as_view(),
                    name="password_change",
                ),
                path(
                    "password_change/done/",
                    auth_views.PasswordChangeDoneView.as_view(),
                    name="password_change_done",
                ),
                path(
                    "password_reset/",
                    auth_views.PasswordResetView.as_view(),
                    name="password_reset",
                ),
                path(
                    "password_reset/done/",
                    auth_views.PasswordResetDoneView.as_view(),
                    name="password_reset_done",
                ),
                path(
                    "reset/<uidb64>/<token>/",
                    auth_views.PasswordResetConfirmView.as_view(),
                    name="password_reset_confirm",
                ),
                path(
                    "reset/done/",
                    auth_views.PasswordResetCompleteView.as_view(),
                    name="password_reset_complete",
                ),
                path(
                    "account/login/",
                    RateLimitedLoginView.as_view(),
                    name="login",
                ),
                path(
                    "logout/",
                    LogoutView.as_view(),
                    name="logout",
                ),
                path(
                    "password_reset/",
                    RateLimitedPasswordResetView.as_view(),
                    name="password_reset",
                ),
                path("", include(tf_urls)),
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
    path("", include("facedetection.urls")),
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
        r"^media/private/(?P<request_path>.*)$", private_media, name="private-media"
    ),
    path("", include("shortlinks.urls")),
    re_path(r"^fp/", include("django_drf_filepond.urls")),
] + static(
    settings.PUBLIC_MEDIA_URL,
    document_root=os.path.join(settings.MEDIA_ROOT, settings.PUBLIC_MEDIA_LOCATION),
)
