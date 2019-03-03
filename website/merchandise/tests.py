from django import test
from django.utils import translation

from . import sitemaps


class SitemapTests(test.SimpleTestCase):
    """Tests the sitemaps"""

    def test_staticviewsitemap(self):
        """Tests the ``:class::merchandise.sitemaps.StaticViewSitemap``"""

        sitemap = sitemaps.StaticViewSitemap()
        items = sitemap.items()
        self.assertNotEqual(items, [])
        for item in items:
            self.assertTrue(item.startswith('merchandise:'))
            self.assertNotEqual(sitemap.location(item), '')


class ViewTests(test.TestCase):
    """Tests the views of this method"""
    fixtures = ['merchandiseitems.json']

    def test_index_en(self):
        """Tests the english index page lists the merchandise items"""
        with translation.override('en'):
            response = self.client.get('/merchandise/')
        self.assertContains(response, 'fancy hat')
        self.assertContains(response, '901.00')
        self.assertContains(response, 'bathrobe')
        self.assertContains(response, '9.00')

    def test_index_nl(self):
        """Tests the english index page lists the merchandise items"""
        response = self.client.get('/merchandise/', HTTP_ACCEPT_LANGUAGE='nl')
        self.assertContains(response, 'Kek hoedje')
        self.assertContains(response, '901,00')
        self.assertContains(response, 'badjas')
        self.assertContains(response, '9,00')
