from django.contrib import sitemaps
from django.urls import reverse


class StaticViewSitemap(sitemaps.Sitemap):
    """Generate the sitemap of the index page."""

    changefreq = "monthly"

    def items(self):
        """Items listed in the sitemap."""
        return ["merchandise:index"]

    def location(self, item):
        """Give the location for the specified item.

        :param item: the item to generate the link to
        :return: the URL to the item
        """
        return reverse(item)


#: The site maps defined by this module
sitemap = {
    "merchandise-static": StaticViewSitemap,
}
