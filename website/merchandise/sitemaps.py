"""Gives sitemaps for the merchandise package"""
from django.contrib import sitemaps
from django.urls import reverse


class StaticViewSitemap(sitemaps.Sitemap):
    """Generates the sitemap of the index page"""

    changefreq = "monthly"

    def items(self):
        """The items listed in the sitemap"""
        return ["merchandise:index"]

    def location(self, item):  # pylint: disable=arguments-differ
        """Gives the location for the specified item

        :param item: the item to generate the link to
        :return: the URL to the item
        """
        return reverse(item)


#: The site maps defined by this module
sitemap = {  # pylint: disable=invalid-name
    "merchandise-static": StaticViewSitemap,
}
