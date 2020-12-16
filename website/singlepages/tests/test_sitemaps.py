import doctest

from singlepages import sitemaps


def load_tests(_loader, tests, _ignore):
    """Load all tests in this module."""
    tests.addTests(doctest.DocTestSuite(sitemaps))
    return tests
