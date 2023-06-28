"""Django settings for concrexit.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import base64
import json
import logging
import os

from django.core.management.commands import makemessages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Sentinel objects that are distinct from None
_NOT_SET = object()


class Misconfiguration(Exception):
    """Exception that is raised when something is misconfigured in this file."""


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "", "..")
)

SOURCE_COMMIT = os.environ.get("SOURCE_COMMIT", "unknown")

# Many of the settings are dependent on the environment we're running in.
# The default environment is development, so the programmer doesn't have to set anything
DJANGO_ENV = os.environ.get("DJANGO_ENV", "development")
_environments = ["production", "staging", "testing", "development"]
if DJANGO_ENV not in _environments:
    raise Misconfiguration(f"Set DJANGO_ENV to one of: {', '.join(_environments)}")


def _set_django_env(env):
    """Set the DJANGO_ENV variable.

    This is a helper function for the doctests below because doctests cannot set global variables.
    """
    global DJANGO_ENV  # noqa: PLW0603
    DJANGO_ENV = env


def setting(*, development, production, staging=_NOT_SET, testing=_NOT_SET):
    """Generate a setting depending on the DJANGO_ENV and the arguments.

    This function is meant for static settings that depend on the DJANGO_ENV. If the
    staging or testing arguments are left to their defaults, they will fall back to
    the production and development settings respectively.

    Example:
        >>> _set_django_env("production")
        >>> SEND_MESSAGES_WITH = setting(development="console", production="mail", staging="DM")
        >>> SEND_MESSAGES_WITH
        'mail'
        >>> _set_django_env("testing")
        >>> setting(development="console", production="mail", staging="DM")
        'console'
    """
    if DJANGO_ENV == "development" or (DJANGO_ENV == "testing" and testing is _NOT_SET):
        return development
    if DJANGO_ENV == "testing":
        return testing
    if DJANGO_ENV == "production" or (DJANGO_ENV == "staging" and staging is _NOT_SET):
        return production
    if DJANGO_ENV == "staging":
        return staging
    raise Misconfiguration(f"Set DJANGO_ENV to one of: {', '.join(_environments)}")


def from_env(
    name, *, production=_NOT_SET, staging=_NOT_SET, testing=_NOT_SET, development=None
):
    """Generate a setting that's overridable by the process environment.

    This will raise an exception if a default is not set for production. Because we use
    the sentinel value _NOT_SET, you can still set a default of None for production if wanted.

    As with :func:`setting` the staging and testing values will fall back to production
    and development. So if an environment variable is required in production, and no default
    is set for staging, staging will also raise the exception.

    Example:
        >>> _set_django_env("production")
        >>> # A secret key should always be set in production via the environment
        >>> from_env("MEDIA_ROOT", development="/media/root")
        Traceback (most recent call last):
          ...
        thaliawebsite.settings.Misconfiguration: Environment variable `MEDIA_ROOT` must be supplied in production
        >>> _set_django_env("development")
        >>> from_env("MEDIA_ROOT", development="/media/root")
        '/media/root'
    """
    try:
        return os.environ[name]
    except KeyError:
        if DJANGO_ENV == "production" or (
            DJANGO_ENV == "staging" and staging is _NOT_SET
        ):
            if production is _NOT_SET and os.environ.get("MANAGE_PY", "0") == "0":
                raise Misconfiguration(
                    f"Environment variable `{name}` must be supplied in production"
                )
            if production is _NOT_SET and os.environ.get("MANAGE_PY", "0") == "1":
                logger.warning(
                    "Ignoring unset %s because we're running a management command", name
                )
                return development
            return production
        if DJANGO_ENV == "staging":
            return staging
        if DJANGO_ENV == "development" or (
            DJANGO_ENV == "testing" and testing is _NOT_SET
        ):
            return development
        if DJANGO_ENV == "testing":
            return testing
        raise Misconfiguration(f"DJANGO_ENV set to unsupported value: {DJANGO_ENV}")


###############################################################################
# Site settings

# We use this setting to generate the email addresses, and for BASE_URL below.
SITE_DOMAIN = from_env("SITE_DOMAIN", development="localhost", production="thalia.nu")

# Used to generate some absolute urls when we don't have access to a request.
BASE_URL = from_env(
    "BASE_URL",
    development=f"http://{SITE_DOMAIN}:8000",
    production=f"https://{SITE_DOMAIN}",
)

# Default FROM email
DEFAULT_FROM_EMAIL = f"{os.environ.get('ADDRESS_NOREPLY', 'noreply')}@{SITE_DOMAIN}"
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = DEFAULT_FROM_EMAIL
NEWSLETTER_FROM_ADDRESS = (
    f"{os.environ.get('ADDRESS_NEWSLETTER', 'newsletter')}@{SITE_DOMAIN}"
)
BOARD_NOTIFICATION_ADDRESS = (
    f"{os.environ.get('ADDRESS_CONTACT', 'info')}@{SITE_DOMAIN}"
)
PARTNER_NOTIFICATION_ADDRESS = (
    f"{os.environ.get('ADDRESS_COLLABORATION', 'samenwerking')}@{SITE_DOMAIN}"
)
EDUCATION_NOTIFICATION_ADDRESS = (
    f"{os.environ.get('ADDRESS_EDUCATION', 'educacie')}@{SITE_DOMAIN}"
)
PROMO_REQUEST_NOTIFICATION_ADDRESS = (
    f"{os.environ.get('ADDRESS_PROMOREQUESTS', 'promocie')}@{SITE_DOMAIN}"
)
TREASURER_NOTIFICATION_ADDRESS = (
    f"{os.environ.get('ADDRESS_TREASURER', 'treasurer')}@{SITE_DOMAIN}"
)


# How many days to keep reference faces after a user marks them for deletion
FACEDETECTION_REFERENCE_FACE_STORAGE_PERIOD_AFTER_DELETE_DAYS = 180

# How many reference faces a user can have at the same time
FACEDETECTION_MAX_NUM_REFERENCE_FACES = 5

# webauthn settings
TWO_FACTOR_WEBAUTHN_RP_NAME = "Thalia"
TWO_FACTOR_WEBAUTHN_RP_ID = SITE_DOMAIN

# ARN of the concrexit-facedetection-lambda function.
# See https://github.com/svthalia/concrexit-facedetection-lambda.
FACEDETECTION_LAMBDA_ARN = os.environ.get("FACEDETECTION_LAMBDA_ARN")

FACEDETECTION_LAMBDA_BATCH_SIZE = int(
    os.environ.get("FACEDETECTION_LAMBDA_BATCH_SIZE", 20)
)

# The scheme the app uses for oauth redirection
APP_OAUTH_SCHEME = os.environ.get("APP_OAUTH_SCHEME", "nu.thalia")

# Membership prices
MEMBERSHIP_PRICES = {
    "year": int(os.environ.get("MEMBERSHIP_PRICE_YEAR_CENTS", "750")) / 100,
    "study": int(os.environ.get("MEMBERSHIP_PRICE_STUDY_CENTS", "3000")) / 100,
}

# Window during which a payment can be deleted again
PAYMENT_CHANGE_WINDOW = int(os.environ.get("PAYMENTS_CHANGE_WINDOW", 10 * 60))

# Payments creditor identifier
SEPA_CREDITOR_ID = os.environ.get("SEPA_CREDITOR_ID", "<unknown>")

# Payment batch withdrawal date default offset after creation date
PAYMENT_BATCH_DEFAULT_WITHDRAWAL_DATE_OFFSET = timezone.timedelta(days=14)

THALIA_PAY_ENABLED_PAYMENT_METHOD = (
    from_env("THALIA_PAY_ENABLED", development="1", staging="1", production="0") == "1"
)
THALIA_PAY_FOR_NEW_MEMBERS = os.environ.get("THALIA_PAY_FOR_NEW_MEMBERS", "1") == "1"

###############################################################################
# Django settings

# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = from_env(
    "SECRET_KEY", development="#o-0d1q5&^&06tn@8pr1f(n3$crafd++^%sacao7hj*ea@c)^t"
)

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    SITE_DOMAIN,
    *from_env("ALLOWED_HOSTS", development="*", production="").split(","),
]

DJANGO_DRF_FILEPOND_UPLOAD_TMP = from_env(
    "DJANGO_DRF_FILEPOND_UPLOAD_TMP",
    development=os.path.join(BASE_DIR, "filepond-temp-uploads"),
)
DJANGO_DRF_FILEPOND_FILE_STORE_PATH = from_env(
    "DJANGO_DRF_FILEPOND_FILE_STORE_PATH",
    development=os.path.join(BASE_DIR, "filepond-uploaded"),
)
DJANGO_DRF_FILEPOND_ALLOW_EXTERNAL_UPLOAD_DIR = True
DJANGO_DRF_FILEPOND_PERMISSION_CLASSES = {
    "GET_FETCH": [
        "oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope",
    ],
    "GET_LOAD": [
        "oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope",
    ],
    "POST_PROCESS": [
        "oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope",
    ],
    "GET_RESTORE": [
        "oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope",
    ],
    "DELETE_REVERT": [
        "oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope",
    ],
    "PATCH_PATCH": [
        "oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope",
    ],
}

# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = from_env("STATIC_ROOT", development=os.path.join(BASE_DIR, "static"))

# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = from_env("MEDIA_ROOT", development=os.path.join(BASE_DIR, "media"))

# https://github.com/johnsensible/django-sendfile#nginx-backend
SENDFILE_URL = "/media/sendfile/"
SENDFILE_ROOT = MEDIA_ROOT
SENDFILE_BACKEND = setting(
    development="django_sendfile.backends.development",
    production="django_sendfile.backends.nginx",
)

PRIVATE_MEDIA_LOCATION = ""
PUBLIC_MEDIA_LOCATION = "public"
STATICFILES_LOCATION = "static"

MEDIA_URL = "/media/private/"

AWS_ACCESS_KEY_ID = from_env("AWS_ACCESS_KEY_ID", production=None)
AWS_SECRET_ACCESS_KEY = from_env("AWS_SECRET_ACCESS_KEY", production=None)
AWS_STORAGE_BUCKET_NAME = from_env("AWS_STORAGE_BUCKET_NAME", production=None)
AWS_DEFAULT_ACL = "private"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_S3_SIGNATURE_VERSION = "s3v4"

if AWS_STORAGE_BUCKET_NAME is not None:
    AWS_CLOUDFRONT_KEY = base64.urlsafe_b64decode(
        os.environ.get("AWS_CLOUDFRONT_KEY", None)
    ).decode("utf-8")
    AWS_CLOUDFRONT_KEY_ID = os.environ.get("AWS_CLOUDFRONT_KEY_ID", None)
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_CLOUDFRONT_DOMAIN", None)

    _STATICFILES_STORAGE = "thaliawebsite.storage.backend.StaticS3Storage"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"

    _DEFAULT_FILE_STORAGE = "thaliawebsite.storage.backend.PrivateS3Storage"

    _PUBLIC_FILE_STORAGE = "thaliawebsite.storage.backend.PublicS3Storage"
    PUBLIC_MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
else:
    _STATICFILES_STORAGE = setting(
        development="django.contrib.staticfiles.storage.StaticFilesStorage",
        production="django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    )
    STATIC_URL = "/static/"

    _DEFAULT_FILE_STORAGE = "thaliawebsite.storage.backend.PrivateFileSystemStorage"

    _PUBLIC_FILE_STORAGE = "thaliawebsite.storage.backend.PublicFileSystemStorage"
    PUBLIC_MEDIA_URL = "/media/public/"

STORAGES = {
    "default": {"BACKEND": _DEFAULT_FILE_STORAGE},
    "public": {"BACKEND": _PUBLIC_FILE_STORAGE},
    "staticfiles": {"BACKEND": _STATICFILES_STORAGE},
}

# https://docs.djangoproject.com/en/dev/ref/settings/#conn-max-age
CONN_MAX_AGE = int(from_env("CONN_MAX_AGE", development="0", production="60"))

# Useful for managing members
# https://docs.djangoproject.com/en/dev/ref/settings/#data-upload-max-number-fields
DATA_UPLOAD_MAX_NUMBER_FIELDS = os.environ.get("DATA_UPLOAD_MAX_NUMBER_FIELDS", 10000)

# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = bool(
    from_env("DJANGO_DEBUG", development=True, production=False, testing=False)
)
# https://docs.djangoproject.com/en/dev/ref/settings/#internal-ips
INTERNAL_IPS = ["127.0.0.1", "172.17.0.1"] if DEBUG else []


def show_toolbar(request):
    return DEBUG


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_toolbar}

# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = setting(development=False, production=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = setting(development=False, production=True)

# https://docs.djangoproject.com/en/dev/ref/settings/#std-setting-SECURE_PROXY_SSL_HEADER
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


###############################################################################
# Celery settings
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#configuration

# Set CELERY_BROKER_URL="redis://127.0.0.1:6379" to use a local redis server in development.
CELERY_BROKER_URL = from_env("CELERY_BROKER_URL")

# Always execute tasks synchronously when no broker is configured in development and testing.
# See https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-task_always_eager
CELERY_TASK_ALWAYS_EAGER = CELERY_BROKER_URL is None


# See https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#caveats
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 18000}

# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
CELERY_BEAT_SCHEDULE = {
    "synchronize_mailinglists": {
        "task": "mailinglists.tasks.sync_mail",
        "schedule": crontab(minute=30),
    },
    "synchronize_moneybird": {
        "task": "moneybirdsynchronization.tasks.synchronize_moneybird",
        "schedule": crontab(minute=30, hour=1),
    },
    "sendpromooverviewweekly": {
        "task": "promotion.tasks.promo_update_weekly",
        "schedule": crontab(minute=0, hour=8, day_of_week=1),
    },
    "sendpromoooverviewdaily": {
        "task": "promotion.tasks.promo_update_daily",
        "schedule": crontab(minute=0, hour=8),
    },
    "facedetectlambda": {
        "task": "facedetection.tasks.trigger_facedetect_lambda",
        "schedule": crontab(minute=0, hour=1),
    },
    "revokeoldmandates": {
        "task": "payments.tasks.revoke_mandates",
        "schedule": crontab(minute=0, hour=1),
    },
    "membershipannouncement": {
        "task": "members.tasks.membership_announcement",
        "schedule": crontab(minute=0, hour=6, day_of_month=31, month_of_year=8),
    },
    "inforequest": {
        "task": "members.tasks.info_request",
        "schedule": crontab(minute=0, hour=6, day_of_month=15, month_of_year=10),
    },
    "expirationannouncement": {
        "task": "members.tasks.expiration_announcement",
        "schedule": crontab(minute=0, hour=6, day_of_month=8, month_of_year=8),
    },
    "minimiseregistration": {
        "task": "registrations.tasks.minimise_registrations",
        "schedule": crontab(minute=0, hour=3, day_of_month=1),
    },
    "sendscheduledmessages": {
        "task": "pushnotifications.tasks.send_scheduled_messages",
        "schedule": crontab(minute="*/2"),
        "args": (120,),
    },
    "revokestaff": {
        "task": "activemembers.tasks.revoke_staff",
        "schedule": crontab(minute=30, hour=3),
    },
    "deletegsuiteusers": {
        "task": "activemembers.tasks.delete_gsuite_users",
        "schedule": crontab(minute=30, hour=3, day_of_week=1),
    },
    "sendplannednewsletters": {
        "task": "newsletters.tasks.send_planned_newsletters",
        "schedule": crontab(minute="*/5"),
    },
    "dataminimisation": {
        "task": "thaliawebsite.tasks.data_minimisation",
        "schedule": crontab(minute=0, hour=3),
    },
    "cleanup": {
        "task": "thaliawebsite.tasks.clean_up",
        "schedule": crontab(minute=0, hour=23),
    },
    "cleartokens": {
        "task": "thaliawebsite.tasks.clear_tokens",
        "schedule": crontab(minute=30, hour=3),
    },
    "sendpromoupdateoverviewdaily": {
        "task": "promotion.tasks.promo_update_overview_daily",
        "schedule": crontab(minute=0, hour=8),
    },
}

###############################################################################
# Email settings
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
_EMAIL_BACKEND = from_env("EMAIL_BACKEND", development="console", production="smtp")
if _EMAIL_BACKEND == "console":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if _EMAIL_BACKEND == "smtp":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST")
    EMAIL_PORT = os.environ.get("DJANGO_EMAIL_PORT", 25)
    EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "1") == "1"
    EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "10"))
    if EMAIL_HOST is None:
        logger.warning(
            "The email host is set to the default of localhost, are you sure you don't want to set EMAIL_HOST?"
        )
        EMAIL_HOST = "localhost"

###############################################################################
# Database settings
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASE_ENGINE = from_env(
    "DATABASE_ENGINE", development="sqlite", production="postgresql", testing=None
)
if DATABASE_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

if DATABASE_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "USER": os.environ.get("POSTGRES_USER", "concrexit"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", None),
            "NAME": os.environ.get("POSTGRES_DB", ""),
            "HOST": os.environ.get("POSTGRES_HOST", ""),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 300,
        }
    }

if DJANGO_ENV == "testing":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "thalia",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "127.0.0.1",
            "PORT": 5432,
        },
    }

###############################################################################
# Firebase config
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "{}")
if FIREBASE_CREDENTIALS != "{}":
    FIREBASE_CREDENTIALS = base64.urlsafe_b64decode(FIREBASE_CREDENTIALS)
FIREBASE_CREDENTIALS = json.loads(FIREBASE_CREDENTIALS)

if FIREBASE_CREDENTIALS != {}:
    from firebase_admin import credentials, initialize_app

    try:
        initialize_app(credential=credentials.Certificate(FIREBASE_CREDENTIALS))
    except ValueError:
        logger.error("Firebase application failed to initialise")

###############################################################################
# GSuite config
GSUITE_ADMIN_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/apps.groups.settings",
]

GSUITE_ADMIN_CREDENTIALS = os.environ.get("GSUITE_ADMIN_CREDENTIALS", "{}")
if GSUITE_ADMIN_CREDENTIALS != "{}":
    GSUITE_ADMIN_CREDENTIALS = base64.urlsafe_b64decode(GSUITE_ADMIN_CREDENTIALS)
GSUITE_ADMIN_CREDENTIALS = json.loads(GSUITE_ADMIN_CREDENTIALS)
GSUITE_ADMIN_USER = os.environ.get("GSUITE_ADMIN_USER", "concrexit-admin@thalia.nu")
GSUITE_DOMAIN = from_env(
    "GSUITE_DOMAIN", development="thalia.localhost", production="thalia.nu"
)
GSUITE_MEMBERS_DOMAIN = from_env(
    "GSUITE_MEMBERS_DOMAIN",
    development="members.thalia.localhost",
    production="members.thalia.nu",
)
GSUITE_MEMBERS_AUTOSYNC = os.environ.get("GSUITE_MEMBERS_AUTOSYNC", "0") == "1"

if GSUITE_ADMIN_CREDENTIALS != {}:
    from google.oauth2 import service_account

    GSUITE_ADMIN_CREDENTIALS = service_account.Credentials.from_service_account_info(
        GSUITE_ADMIN_CREDENTIALS, scopes=GSUITE_ADMIN_SCOPES
    ).with_subject(GSUITE_ADMIN_USER)

EMAIL_DOMAIN_BLACKLIST = [GSUITE_MEMBERS_DOMAIN]

###############################################################################
# Google maps API key and secrets
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
GOOGLE_MAPS_API_SECRET = os.environ.get("GOOGLE_MAPS_API_SECRET", "")
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

###############################################################################
# Sentry setup
if "SENTRY_DSN" in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        release=SOURCE_COMMIT,
        send_default_pii=True,
        environment=DJANGO_ENV,
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", 0.2)),
        profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", 0.0)),
    )


###############################################################################
# (Mostly) static settings
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Dependencies
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "formtools",
    "two_factor",
    "oauth2_provider",
    "corsheaders",
    "django_bootstrap5",
    "tinymce",
    "rest_framework",
    "rest_framework.authtoken",
    "debug_toolbar",
    "sass_processor",
    "admin_auto_filters",
    "django_drf_filepond",
    "django_filepond_widget",
    "thumbnails",
    # Our apps
    # Directly link to the app config when applicable as recommended
    # by the docs: https://docs.djangoproject.com/en/2.0/ref/applications/
    "thaliawebsite.apps.ThaliaWebsiteConfig",  # include for admin settings
    # Load django.contrib.admin after thaliawebsite so the admin page gets modified
    "django.contrib.admin",
    # Our apps ordered such that templates in the first
    # apps can override those used by the later apps.
    "pushnotifications.apps.PushNotificationsConfig",
    "facedetection.apps.FaceDetectionConfig",
    "announcements.apps.AnnouncementsConfig",
    "promotion.apps.PromotionConfig",
    "members.apps.MembersConfig",
    "documents.apps.DocumentsConfig",
    "activemembers.apps.ActiveMembersConfig",
    "photos.apps.PhotosConfig",
    "utils",
    "mailinglists.apps.MailinglistsConfig",
    "merchandise.apps.MerchandiseConfig",
    "thabloid.apps.ThabloidConfig",
    "partners.apps.PartnersConfig",
    "events.apps.EventsConfig",
    "pizzas.apps.PizzasConfig",
    "newsletters.apps.NewslettersConfig",
    "education.apps.EducationConfig",
    "registrations.apps.RegistrationsConfig",
    "payments.apps.PaymentsConfig",
    "singlepages.apps.SinglepagesConfig",
    "shortlinks.apps.ShortLinkConfig",
    "sales.apps.SalesConfig",
    "moneybirdsynchronization.apps.MoneybirdsynchronizationConfig",
    "two_factor.plugins.webauthn",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "thaliawebsite.middleware.RealIPMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
    "members.middleware.MemberMiddleware",
    "announcements.middleware.AnnouncementMiddleware",
]

if DJANGO_ENV in ("development", "testing"):
    INSTALLED_APPS += [
        "django_template_check",
        "django_extensions",
    ]

if DJANGO_ENV == "testing":
    for x in (
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        "django.middleware.http.ConditionalGetMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
    ):
        MIDDLEWARE.remove(x)
    for x in ("debug_toolbar",):
        INSTALLED_APPS.remove(x)

ROOT_URLCONF = "thaliawebsite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": setting(development=True, production=False),
        "OPTIONS": {
            "context_processors": [
                "thaliawebsite.context_processors.source_commit",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "announcements.context_processors.announcements",
                "thaliawebsite.context_processors.aprilfools",
                "thaliawebsite.context_processors.lustrum_styling",
            ],
        },
    },
]

if DJANGO_ENV in ["production", "staging"]:
    # Use caching template loader
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        )
    ]

# Default logging: https://github.com/django/django/blob/master/django/utils/log.py
# We disable mailing the admin.
# Server errors will be sent to Sentry via the config below this.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

REDIS_CACHE_PORT = int(
    from_env("REDIS_CACHE_PORT", development="6379", production="6379")
)
REDIS_CACHE_HOST = from_env("REDIS_CACHE_HOST")
REDIS_CACHE_URL = (
    f"redis://{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}" if REDIS_CACHE_HOST else None
)

CACHES = {
    "default": (
        {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_CACHE_URL,
        }
        if REDIS_CACHE_URL is not None
        else {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_default_db_cache",
        }
    ),
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

WSGI_APPLICATION = "thaliawebsite.wsgi.application"

# Login pages
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "/"

# Cors configuration
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(?:api/v1|api/v2|user/oauth)/.*"

# OAuth configuration
OIDC_RSA_PRIVATE_KEY = from_env("OIDC_RSA_PRIVATE_KEY", testing=None)
if OIDC_RSA_PRIVATE_KEY is not None:
    OIDC_RSA_PRIVATE_KEY = base64.urlsafe_b64decode(OIDC_RSA_PRIVATE_KEY).decode()

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "OIDC_RSA_PRIVATE_KEY": OIDC_RSA_PRIVATE_KEY,
    "ALLOWED_REDIRECT_URI_SCHEMES": setting(
        production=["https", APP_OAUTH_SCHEME],
        staging=["http", "https", APP_OAUTH_SCHEME],
        development=["http", "https", APP_OAUTH_SCHEME],
    ),
    "SCOPES": {
        "openid": "OpenID Connect",
        "read": "Authenticated read access to the website",
        "write": "Authenticated write access to the website",
        "activemembers:read": "Read access to committee, society and board groups",
        "announcements:read": "Read access to announcements",
        "events:read": "Read access to events and your event registrations",
        "events:register": "Write access to the state of your event registrations",
        "events:admin": "Admin access to the events",
        "facedetection:read": "Read access to facedetection",
        "facedetection:write": "Write access to facedetection",
        "food:read": "Read access to food events",
        "food:order": "Order access to food events",
        "food:admin": "Admin access to food events",
        "members:read": "Read access to the members directory",
        "photos:read": "Read access to photos",
        "profile:read": "Read access to your member profile",
        "profile:write": "Write access to your member profile",
        "pushnotifications:read": "Read access to push notifications",
        "pushnotifications:write": "Write access to push notifications",
        "partners:read": "Read access to partners",
        "payments:read": "Read access to payments",
        "payments:write": "Write access to payments",
        "payments:admin": "Admin access to payments",
        "sales:read": "Read access to your Point of Sale orders",
        "sales:order": "Place Point of Sale orders on your behalf",
        "sales:admin": "Admin access to Point of Sale orders",
    },
}

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth."
            "password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),
    },
]

PASSWORD_HASHERS = setting(
    development=(
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ),
    production=(
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
        "django.contrib.auth.hashers.BCryptPasswordHasher",
    ),
    testing=("django.contrib.auth.hashers.MD5PasswordHasher",),
)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "activemembers.backends.MemberGroupBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "thaliawebsite.api.authentication.APIv1TokenAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "thaliawebsite.api.pagination.APIv2LimitOffsetPagination",
    "PAGE_SIZE": 50,  # Only for API v2
    "ALLOWED_VERSIONS": ["v1", "v2", "calendarjs", "facedetection"],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_SCHEMA_CLASS": "thaliawebsite.api.openapi.OAuthAutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "thaliawebsite.api.throttling.AnonRateThrottle",
        "thaliawebsite.api.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": setting(
        production={"anon": "30/min", "user": "90/min"},
        staging={"anon": "30/min", "user": "90/min"},
        development={"anon": None, "user": None},
    ),
}

# Rate limiting
RATELIMIT_VIEW = "thaliawebsite.views.rate_limited_view"

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
USE_I18N = True
LANGUAGES = [("en", _("English"))]
LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Amsterdam"

# We provide formatting overrides in the `thaliawebsite.en.formats`, because Django
# no longer supports running without localization. This works to enforce the same format
# regardless of the user's language/locale, because `en` is the only enabled language.
FORMAT_MODULE_PATH = ["thaliawebsite.locale"]

# Static files
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
)

# Allow importing .scss files that don't start with an underscore.
# See https://github.com/jrief/django-sass-processor
SASS_PROCESSOR_INCLUDE_FILE_PATTERN = r"^.+\.scss$"

# See utils/model/signals.py for explanation
SUSPEND_SIGNALS = False

THUMBNAILS_METADATA = (
    {
        "BACKEND": "thumbnails.backends.metadata.RedisBackend",
        "host": REDIS_CACHE_HOST,
        "port": REDIS_CACHE_PORT,
    }
    if REDIS_CACHE_HOST
    else {
        "BACKEND": "thumbnails.backends.metadata.DatabaseBackend",
    }
)

THUMBNAILS = {
    "METADATA": THUMBNAILS_METADATA,
    "STORAGE": {
        # django-thumbnails does not use the Django 4.2 `storages` API yet,
        # but we can simply give it the path as we would with the new API.
        "BACKEND": _DEFAULT_FILE_STORAGE,
    },
    "SIZES": {
        "small": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (300, 300),
                    "mode": "cover",
                },
            ],
        },
        "medium": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (600, 600),
                    "mode": "cover",
                },
            ],
        },
        "large": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (1200, 900),
                    "mode": "cover",
                },
            ],
        },
        "photo_medium": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (1200, 900),
                },
            ],
        },
        "photo_large": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (1920, 1920),
                },
            ],
        },
        "avatar_large": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (900, 900),
                    "mode": "cover",
                },
            ],
        },
        "slide_small": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (500, 108),
                    "mode": "cover",
                },
            ],
        },
        "slide_medium": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (1000, 215),
                    "mode": "cover",
                },
            ],
        },
        "slide": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (2000, 430),
                    "mode": "cover",
                },
            ],
        },
        "fit_small": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (300, 300),
                },
            ],
        },
        "fit_medium": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (600, 600),
                },
            ],
        },
        "fit_medium_pad": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (600, 250),
                    "mode": "pad",
                },
            ],
        },
        "fit_small_pad": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (360, 150),
                    "mode": "pad",
                },
            ],
        },
        "fit_large": {
            "FORMAT": "webp",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.thumbnail",
                    "size": (1200, 900),
                },
            ],
        },
        "source": {
            "FORMAT": "jpg",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.process_upload",
                    "size": (8_000, 8_000),
                    "format": "jpg",
                }
            ],
        },
        "source_png": {
            "FORMAT": "png",
            "PROCESSORS": [
                {
                    "PATH": "utils.media.processors.process_upload",
                    "size": (8_000, 8_000),
                    "format": "png",
                }
            ],
        },
    },
}

THUMBNAIL_SIZES = set(THUMBNAILS["SIZES"].keys())

# TinyMCE config
TINYMCE_DEFAULT_CONFIG = {
    "max_height": 500,
    "menubar": False,
    "plugins": "autolink autoresize link image code media paste lists",
    "toolbar": "h2 h3 | bold italic underline strikethrough | image media | link unlink "
    "| bullist numlist | undo redo | code",
    "contextmenu": "bold italic underline strikethrough | link",
    "paste_as_text": True,
    "relative_urls": False,
    "remove_script_host": False,
    "autoresize_bottom_margin": 50,
}
TINYMCE_EXTRA_MEDIA = {
    "css": {
        "all": [
            "css/tinymce.css",
        ],
    },
}


BOOTSTRAP5 = {"required_css_class": "required-field"}

# https://docs.djangoproject.com/en/dev/ref/settings/#default-exception-reporter-filter
DEFAULT_EXCEPTION_REPORTER_FILTER = (
    "utils.exception_filter.ThaliaSafeExceptionReporterFilter"
)

# Make sure the locations in django.po files don't include line nrs.
makemessages.Command.xgettext_options.append("--add-location=file")

GRAPH_MODELS = {
    "all_applications": False,
    "group_models": True,
    "app_labels": [
        "events",
        "photos",
        "merchandise",
        "thabloid",
        "partners",
        "newsletters",
        "shortlinks",
        "promotion",
        "documents",
        "pizzas",
        "announcements",
        "sales",
        "registrations",
        "mailinglists",
        "payments",
        "members",
        "admin",
        "pushnotifications",
        "activemembers",
        "education",
        "auth",
    ],
}

MONEYBIRD_START_DATE = os.environ.get("MONEYBIRD_START_DATE", "2023-09-01")

MONEYBIRD_ADMINISTRATION_ID: int | None = (
    int(os.environ.get("MONEYBIRD_ADMINISTRATION_ID"))
    if os.environ.get("MONEYBIRD_ADMINISTRATION_ID")
    else None
)

MONEYBIRD_API_KEY = os.environ.get("MONEYBIRD_API_KEY")

MONEYBIRD_SYNC_ENABLED = MONEYBIRD_ADMINISTRATION_ID and MONEYBIRD_API_KEY

MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID: int | None = (
    int(os.environ.get("MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID"))
    if os.environ.get("MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID")
    else None
)
MONEYBIRD_UNKNOWN_PAYER_CONTACT_ID: int | None = (
    int(os.environ.get("MONEYBIRD_UNKNOWN_PAYER_CONTACT_ID"))
    if os.environ.get("MONEYBIRD_UNKNOWN_PAYER_CONTACT_ID")
    else None
)
MONEYBIRD_CONTRIBUTION_LEDGER_ID: int | None = (
    int(os.environ.get("MONEYBIRD_CONTRIBUTION_LEDGER_ID"))
    if os.environ.get("MONEYBIRD_CONTRIBUTION_LEDGER_ID")
    else None
)

MONEYBIRD_TPAY_FINANCIAL_ACCOUNT_ID: int | None = (
    int(os.environ.get("MONEYBIRD_TPAY_FINANCIAL_ACCOUNT_ID"))
    if os.environ.get("MONEYBIRD_TPAY_FINANCIAL_ACCOUNT_ID")
    else None
)
MONEYBIRD_CASH_FINANCIAL_ACCOUNT_ID: int | None = (
    int(os.environ.get("MONEYBIRD_CASH_FINANCIAL_ACCOUNT_ID"))
    if os.environ.get("MONEYBIRD_CASH_FINANCIAL_ACCOUNT_ID")
    else None
)
MONEYBIRD_CARD_FINANCIAL_ACCOUNT_ID: int | None = (
    int(os.environ.get("MONEYBIRD_CARD_FINANCIAL_ACCOUNT_ID"))
    if os.environ.get("MONEYBIRD_CARD_FINANCIAL_ACCOUNT_ID")
    else None
)

MONEYBIRD_ZERO_TAX_RATE_ID: int | None = (
    int(os.environ.get("MONEYBIRD_ZERO_TAX_RATE_ID"))
    if os.environ.get("MONEYBIRD_ZERO_TAX_RATE_ID")
    else None
)
