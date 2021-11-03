from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap of the static thabloid index page."""

    changefreq = "monthly"

    def items(self):
        """Return the index url name."""
        return ["thabloid:index"]

    def location(self, item):
        """Return the index url."""
        return reverse(item)


class ThabloidSitemap(sitemaps.Sitemap):
    """Sitemap of the thabloid pages."""

    changefreq = "never"

    def items(self):
        """Return all Thabloids."""
        return models.Thabloid.objects.all()

    def location(self, item):
        """Return the url of a Thabloid."""
        return item.get_absolute_url()


sitemap = {
    "thabloid-static": StaticViewSitemap,
    "thabloid-thabloids": ThabloidSitemap,
}
