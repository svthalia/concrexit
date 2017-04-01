import doctest

from . import views


def load_tests(loader, tests, ignore):
    """
    Load all tests in this module
    """
    # Adds the doctests in views
    tests.addTests(doctest.DocTestSuite(views))
    return tests
