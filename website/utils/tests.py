"""Tests for the ``utils`` module."""
import doctest

from utils import snippets


def load_tests(_loader, tests, _ignore):
    """Load all tests in this module."""
    # Adds the doctests in snippets
    tests.addTests(doctest.DocTestSuite(snippets))
    return tests
