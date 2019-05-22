"""
Thalia's root URL Configuration

The ``urlpatterns`` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/dev/topics/http/urls/

Examples:

* Function views

  1. Add an import: ``from my_app import views``
  2. Add a URL to ``urlpatterns``: ``url(r'^$', views.home, name='home')``

* Class-based views

  1. Add an import: ``from other_app.views import Home``
  2. Add a URL to urlpatterns: ``url(r'^$', Home.as_view(), name='home')``

* Including another URLconf

  1. Import the ``include()`` function::

        from django.conf.urls import url, include

  2. Add a URL to urlpatterns: ``url(r'^blog/', include('blog.urls'))``
"""

# pragma: noqa

import os.path

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.i18n import JavaScriptCatalog

import members
from activemembers.sitemaps import sitemap as activemembers_sitemap
from documents.sitemaps import sitemap as documents_sitemap
from events.sitemaps import sitemap as events_sitemap
from events.views import AlumniEventsView
from members.sitemaps import sitemap as members_sitemap
from members.views import ObtainThaliaAuthToken
from partners.sitemaps import sitemap as partners_sitemap
from thabloid.sitemaps import sitemap as thabloid_sitemap
from thaliawebsite.forms import AuthenticationForm
from thaliawebsite.views import (
    PrivacyPolicyView, EventTermsView,
    SiblingAssociationsView, TestCrashView,
    ContactView, IndexView,
    BecomeActiveView,
    StyleGuideView
)
from utils.media.views import (generate_thumbnail, private_media)
from .sitemaps import StaticViewSitemap

__all__ = ['urlpatterns']

THALIA_SITEMAP = {
    'main-static': StaticViewSitemap,
}
THALIA_SITEMAP.update(activemembers_sitemap)
THALIA_SITEMAP.update(members_sitemap)
THALIA_SITEMAP.update(documents_sitemap)
THALIA_SITEMAP.update(thabloid_sitemap)
THALIA_SITEMAP.update(partners_sitemap)
THALIA_SITEMAP.update(events_sitemap)

# pragma pylint: disable=line-too-long
urlpatterns = [  # pylint: disable=invalid-name
    url(r'^admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('event-registration-terms/', EventTermsView.as_view(), name='event-registration-terms'),
    path('alumni/', AlumniEventsView.as_view(), name='alumni'),
    url(r'^registration/', include('registrations.urls')),
    url(r'^events/', include('events.urls')),
    url(r'^pizzas/', include('pizzas.urls')),
    url(r'^newsletters/', include('newsletters.urls')),
    url(r'^', include([  # 'association' menu
        url(r'^', include('activemembers.urls')),
        url(r'^merchandise/', include('merchandise.urls')),
        url(r'^documents/', include('documents.urls')),
        path('sibling-associations/', SiblingAssociationsView.as_view(), name='sibling-associations'),
        url(r'^thabloid/', include('thabloid.urls')),
    ])),
    url(r'^', include([  # 'for members' menu
        path('become-active/', BecomeActiveView.as_view(), name='become-active'),
        url(r'^photos/', include('photos.urls')),
        path('statistics/', members.views.statistics, name='statistics'),
        path('styleguide/', StyleGuideView.as_view(), name='styleguide'),
    ])),
    url(r'^career/', include('partners.urls')),
    url(r'^contact$', ContactView.as_view(), name='contact'),
    url(r'^api/', include([
        url(r'^v1/', include([
            url(r'^token-auth', ObtainThaliaAuthToken.as_view()),
            url(r'^', include('activemembers.api.urls')),
            url(r'^', include('events.api.urls')),
            url(r'^', include('members.api.urls')),
            url(r'^', include('partners.api.urls')),
            url(r'^', include('mailinglists.api.urls')),
            url(r'^', include('pizzas.api.urls')),
            url(r'^', include('photos.api.urls')),
            url(r'^', include('pushnotifications.api.urls')),
        ])),
    ])),
    url(r'^education/', include('education.urls')),
    url(r'^announcements/', include('announcements.urls')),
    url(r'^pushnotifications/', include('pushnotifications.urls')),
    # Default login helpers
    url(r'^login/$', LoginView.as_view(), {'authentication_form': AuthenticationForm},
        name='login'),
    url(r'^user/', include('django.contrib.auth.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    # Sitemap
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': THALIA_SITEMAP},
        name='django.contrib.sitemaps.views.sitemap'),
    # Dependencies
    url(r'^tinymce/', include('tinymce.urls')),
    # Javascript translation catalog
    url(r'jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    # Provide something to test error handling. Limited to admins.
    path('crash/', TestCrashView.as_view()),
    # Custom media paths
    url(r'^media/generate-thumbnail/(?P<request_path>.*)', generate_thumbnail, name='generate-thumbnail'),
    url(r'^media/private/(?P<request_path>.*)$', private_media, name='private-media'),
    url('', include('members.urls')),
    url('', include('payments.urls')),
] + static(settings.MEDIA_URL + 'public/',
           document_root=os.path.join(settings.MEDIA_ROOT, 'public'))
