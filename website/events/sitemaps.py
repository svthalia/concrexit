"""The sitemaps defined by the events package"""
from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap of the static event pages"""

    changefreq = "daily"

    def items(self):
        return ["events:index"]

    def location(self, obj):
        return reverse(obj)


class EventSitemap(sitemaps.Sitemap):
    """Sitemap of the event detail pages"""

    def items(self):
        return models.Event.objects.filter(published=True)

    def location(self, obj):
        return obj.get_absolute_url()


sitemap = {
    "events-static": StaticViewSitemap,
    "events-events": EventSitemap,
}
