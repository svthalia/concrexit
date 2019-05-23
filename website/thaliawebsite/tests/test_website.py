"""Tests for things provided by this module"""
import doctest

from django.test import TestCase

from thaliawebsite import sitemaps
from thaliawebsite.templatetags import bleach_tags


def load_tests(_loader, tests, _ignore):
    """
    Load all tests in this module
    """
    # Adds the doctests in bleach_tags
    tests.addTests(doctest.DocTestSuite(bleach_tags))
    tests.addTests(doctest.DocTestSuite(sitemaps))
    return tests


class SitemapTest(TestCase):
    fixtures = ['members.json', 'member_groups.json']

    def test_sitemap_success(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
