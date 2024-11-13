from django.contrib import sitemaps
from django.urls import reverse


class StaticViewSitemap(sitemaps.Sitemap):
    """Static sitemap with members page."""

    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["members:index"]

    def location(self, item):
        return reverse(item)


sitemap = {
    "members-static": StaticViewSitemap,
}
