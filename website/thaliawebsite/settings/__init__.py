"""
Settings module

This file controls what settings are loaded.

Using environment variables you can control the loading of various
overrides.
"""
# flake8: noqa: ignore F403
import logging
from firebase_admin import initialize_app, credentials

# Load all default settings because we need to use settings.configure
# for sphinx documentation generation.
from django.conf.global_settings import *  # pylint: disable=wildcard-import

# Load base settings
from .settings import *  # pylint: disable=wildcard-import

logger = logging.getLogger(__name__)

# Attempt to load local overrides
try:
    from .localsettings import *  # pylint: disable=wildcard-import
except ImportError:
    pass

# Load production settings if DJANGO_PRODUCTION is set
if os.environ.get('DJANGO_PRODUCTION'):  # pragma: nocover
    from .production import *  # pylint: disable=wildcard-import

# Load testing settings if GITLAB_CI is set
if os.environ.get('GITLAB_CI'):  # pragma: nocover
    from .testing import *  # pylint: disable=wildcard-import

try:
    initialize_app(
        credential=credentials.Certificate(FIREBASE_CREDENTIALS))
except ValueError as e:
    logger.error('Firebase application failed to initialise')
