from django import test

from . import sitemaps


class SitemapTests(test.SimpleTestCase):
    """Tests the sitemaps."""

    def test_staticviewsitemap(self):
        """Tests the ``:class::merchandise.sitemaps.StaticViewSitemap``."""
        sitemap = sitemaps.StaticViewSitemap()
        items = sitemap.items()
        self.assertNotEqual(items, [])
        for item in items:
            self.assertTrue(item.startswith("merchandise:"))
            self.assertNotEqual(sitemap.location(item), "")
