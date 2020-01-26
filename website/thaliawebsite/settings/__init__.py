"""
Settings module

This file controls what settings are loaded.

Using environment variables you can control the loading of various
overrides.
"""
import logging
from firebase_admin import initialize_app, credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Load all default settings because we need to use settings.configure
# for sphinx documentation generation.
from django.conf.global_settings import *

# Load base settings
from .settings import *

logger = logging.getLogger(__name__)

# Attempt to load local overrides
try:
    from .localsettings import *
except ImportError:
    pass

# Load production settings if DJANGO_PRODUCTION is set
if os.environ.get("DJANGO_PRODUCTION"):  # pragma: nocover
    from .production import *

# Load testing settings if GITLAB_CI is set
if os.environ.get("GITLAB_CI"):  # pragma: nocover
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
