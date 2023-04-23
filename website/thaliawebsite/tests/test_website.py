"""Tests for things provided by this module."""
import doctest

from django.test import TestCase, override_settings

from thaliawebsite import settings, sitemaps
from thaliawebsite.templatetags import bleach_tags


def load_tests(_loader, tests, _ignore):
    """Load all tests in this module."""
    # Adds the doctests in bleach_tags
    tests.addTests(doctest.DocTestSuite(bleach_tags))
    tests.addTests(doctest.DocTestSuite(sitemaps))
    tests.addTests(doctest.DocTestSuite(settings))
    return tests


@override_settings(SUSPEND_SIGNALS=True)
class SitemapTest(TestCase):
    fixtures = [
        "members.json",
        "member_groups.json",
    ]

    def test_sitemap_success(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
