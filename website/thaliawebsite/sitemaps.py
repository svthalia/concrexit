"""Defines site maps."""
from django.contrib import sitemaps
from django.urls import reverse


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap items for static pages."""

    def items(self):
        """Return items of the site map.

        >>> sitemap = StaticViewSitemap()
        >>> sitemap.items()[0]
        'index'

        :return: the items in the site map
        :rtype: [str]
        """
        # Need to be valid entries for reverse()
        return ["index"]

    def location(self, obj):
        """Get the location for a site map item.

        Example::

            >>> sitemap = StaticViewSitemap()
            >>> sitemap.location('index')
            '/'

        :param obj: the item to reverse.
        :type obj: str
        :return: the URI to the item.
        """
        return reverse(obj)
