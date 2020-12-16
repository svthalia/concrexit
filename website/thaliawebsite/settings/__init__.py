"""Settings module.

This file controls what settings are loaded.

Using environment variables you can control the loading of various
overrides.
"""
import logging
from firebase_admin import initialize_app, credentials
from google.oauth2 import service_account


# Load base settings
# pylint: disable=wrong-import-position
from .settings import *

logger = logging.getLogger(__name__)

# Attempt to load local overrides
try:
    from .localsettings import *
except ImportError:
    pass

# Load production settings if DJANGO_PRODUCTION is set
if os.environ.get("DJANGO_PRODUCTION"):
    from .production import *

# Load testing settings if GITHUB_ACTIONS is set
if os.environ.get("GITHUB_ACTIONS"):
    from .testing import *

if FIREBASE_CREDENTIALS != {}:
    try:
        initialize_app(credential=credentials.Certificate(FIREBASE_CREDENTIALS))
    except ValueError as e:
        logger.error("Firebase application failed to initialise")


if GSUITE_ADMIN_CREDENTIALS != {}:
    GSUITE_ADMIN_CREDENTIALS = service_account.Credentials.from_service_account_info(
        GSUITE_ADMIN_CREDENTIALS, scopes=GSUITE_ADMIN_SCOPES
    ).with_subject(GSUITE_ADMIN_USER)
