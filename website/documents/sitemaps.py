from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap for the static pages."""

    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["documents:index"]

    def location(self, item):
        return reverse(item)


class MiscellaneousDocumentsSitemap(sitemaps.Sitemap):
    """Sitemap for misc documents."""

    def items(self):
        return models.MiscellaneousDocument.objects.exclude(members_only=True)

    def location(self, item):
        return item.get_absolute_url()


sitemap = {
    "documents-static": StaticViewSitemap,
    "documents-miscellaneous": MiscellaneousDocumentsSitemap,
}
