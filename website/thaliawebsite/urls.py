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
from django.contrib.auth.views import login
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from rest_framework.authtoken import views as rfviews

import members
from activemembers.sitemaps import sitemap as activemembers_sitemap
from documents.sitemaps import sitemap as documents_sitemap
from events.feeds import DeprecationFeed
from events.sitemaps import sitemap as events_sitemap
from members.sitemaps import sitemap as members_sitemap
from partners.sitemaps import sitemap as partners_sitemap
from thabloid.sitemaps import sitemap as thabloid_sitemap
from thaliawebsite.forms import AuthenticationForm
from utils.views import private_thumbnails, generate_thumbnail
from . import views
from .sitemaps import StaticViewSitemap

thalia_sitemap = {
    'main-static': StaticViewSitemap,
}
thalia_sitemap.update(activemembers_sitemap)
thalia_sitemap.update(members_sitemap)
thalia_sitemap.update(documents_sitemap)
thalia_sitemap.update(thabloid_sitemap)
thalia_sitemap.update(partners_sitemap)
thalia_sitemap.update(events_sitemap)

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^mailinglists/', include('mailinglists.urls')),
    url(r'^members/', include('members.urls')),
    url(r'^account/$', members.views.account, name='account'),
    url(r'^events/', include('events.urls')),
    url(r'^pizzas/', include('pizzas.urls')),
    url(r'^', include([  # 'deprecated ical feeds' menu
        url(r'^index\.php/events/ical/feed\.ics', DeprecationFeed()),
        url(r'^nieuws/agenda/vcal\.php', DeprecationFeed()),
    ])),
    url(r'^newsletters/', include('newsletters.urls')),
    url(r'^nieuwsbrief/', include('newsletters.urls', namespace='newsletters-legacy'),),  # for legacy reasons
    url(r'^association$', TemplateView.as_view(
        template_name='singlepages/association.html'), name='association'),
    url(r'^', include([  # 'association' menu
        url(r'^', include('activemembers.urls')),
        url(r'^merchandise/', include('merchandise.urls')),
        url(r'^documents/', include('documents.urls')),
        url(r'^become-a-member/', members.views.become_a_member, name='become-a-member'),
        url(r'^sister-associations', TemplateView.as_view(template_name='singlepages/sister_associations.html'), name='sister-associations'),
        url(r'^thabloid/', include('thabloid.urls')),
    ])),
    url(r'^for-members$', TemplateView.as_view(
        template_name='singlepages/for_members.html'), name='for-members'),
    url(r'^', include([  # 'for members' menu
        url(r'^become-active/', TemplateView.as_view(template_name='singlepages/become_active.html'), name='become-active'),
        url(r'^photos/', include('photos.urls')),
        url(r'^statistics/$', members.views.statistics, name='statistics'),
        url(r'^styleguide/$', views.styleguide, name='styleguide'),
        url(r'^styleguide/file/(?P<filename>[\w\-_\.]+)$', views.styleguide_file, name='styleguide-file'),
    ])),
    url(r'^career/', include('partners.urls')),
    url(r'^contact$', TemplateView.as_view(template_name='singlepages/contact.html'), name='contact'),
    url(r'^private-thumbnails/(?P<size_fit>\d+x\d+_[01])/(?P<path>.*)', private_thumbnails, name='private-thumbnails'),
    url(r'^generate-thumbnail/(?P<size_fit>\d+x\d+_[01])/(?P<path>[^/]+)/(?P<thumbpath>[^/]+)', generate_thumbnail, name='generate-thumbnail'),
    url(r'^api/', include([
        url(r'wikilogin', views.wiki_login),
        url(r'^v1/', include([
            url(r'^token-auth', rfviews.obtain_auth_token),
            url(r'^', include('events.api.urls')),
            url(r'^', include('members.api.urls')),
            url(r'^', include('partners.api.urls')),
        ], namespace='v1')),
    ])),
    url(r'^education/', include('education.urls')),
    url(r'^announcements/', include('announcements.urls')),
    # Default login helpers
    url(r'^login/$', login, {'authentication_form': AuthenticationForm},
        name='login'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    # Sitemap
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': thalia_sitemap},
        name='django.contrib.sitemaps.views.sitemap'),
    # Dependencies
    url(r'^tinymce/', include('tinymce.urls')),
    # Javascript translation catalog
    url(r'jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    # XXX
    url(r'crash/$', views.crash),
] + static(settings.MEDIA_URL + 'public/',
           document_root=os.path.join(settings.MEDIA_ROOT, 'public'))
