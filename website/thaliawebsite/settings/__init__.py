"""
Settings module

This file controls what settings are loaded.

Using environment variables you can control the loading of various
overrides.
"""

# flake8: noqa
import os

# Load base settings
from .settings import *

# Attempt to load local overrides
try:
    from .localsettings import *
except ImportError:
    pass

# Load production settings if DJANGO_PRODUCTION is set
if os.environ.get('DJANGO_PRODUCTION'):  # pragma: nocover
    from .production import *

# Load testing settings if GITLAB_CI is set
if os.environ.get('GITLAB_CI'):  # pragma: nocover
    from .testing import *
