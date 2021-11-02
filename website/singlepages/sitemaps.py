"""Defines site maps."""
from django.contrib import sitemaps
from django.urls import reverse


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap items for static pages."""

    def items(self):
        """Return the items of the site map.

        >>> sitemap = StaticViewSitemap()
        >>> sitemap.items()[0]
        'singlepages:become-active'

        :return: the items in the site map
        :rtype: [str]
        """
        # Need to be valid entries for reverse()
        return [
            "singlepages:become-active",
            "singlepages:sibling-associations",
            "singlepages:contact",
        ]

    def location(self, item):
        """Get the location for a site map item.

        Example::

            >>> sitemap = StaticViewSitemap()
            >>> sitemap.location('singlepages:become-active')
            '/members/become-active/'

        :param item: the item to reverse.
        :type item: str
        :return: the URI to the item.
        """
        return reverse(item)


sitemap = {
    "singlepages-static": StaticViewSitemap,
}
