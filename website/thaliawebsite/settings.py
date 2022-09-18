"""Django settings for concrexit.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import logging

import base64
import json
import os

from django.core.management.commands import makemessages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
    # pylint: disable=global-statement
    global DJANGO_ENV
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
                # pylint: disable=raise-missing-from
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
        # pylint: disable=raise-missing-from
        raise Misconfiguration(f"DJANGO_ENV set to unsupported value: {DJANGO_ENV}")


###############################################################################
# Site settings

# We use this setting to generate the email addresses
SITE_DOMAIN = from_env(
    "SITE_DOMAIN", development="thalia.localhost", production="thalia.nu"
)
# We use this domain to generate some absolute urls when we don't have access to a request
BASE_URL = os.environ.get("BASE_URL", f"https://{SITE_DOMAIN}")

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
    f"{os.environ.get('ADDRESS_PROMOREQUESTS', 'paparazcie')}@{SITE_DOMAIN}"
)
PROMO_PUBLISH_DATE_TIMEDELTA = timezone.timedelta(weeks=1)

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
# https://docs.djangoproject.com/en/dev/ref/settings/#internal-ips
INTERNAL_IPS = setting(development=["127.0.0.1", "172.17.0.1"], production=[])

# https://django-compressor.readthedocs.io/en/stable/settings/#django.conf.settings.COMPRESS_OFFLINE
COMPRESS_OFFLINE = setting(development=False, production=True)

# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = from_env("STATIC_ROOT", development=os.path.join(BASE_DIR, "static"))

SENDFILE_BACKEND = setting(
    development="django_sendfile.backends.development",
    production="django_sendfile.backends.nginx",
)
# https://github.com/johnsensible/django-sendfile#nginx-backend
SENDFILE_URL = "/media/sendfile/"
SENDFILE_ROOT = from_env(
    "SENDFILE_ROOT",
    production="/concrexit/media/",
    development=os.path.join(BASE_DIR, "media"),
)

# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/private/"
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = from_env("MEDIA_ROOT", development=os.path.join(BASE_DIR, "media"))

PRIVATE_MEDIA_LOCATION = ""
PUBLIC_MEDIA_LOCATION = "public"

AWS_ACCESS_KEY_ID = from_env("AWS_ACCESS_KEY_ID", production=None)
AWS_SECRET_ACCESS_KEY = from_env("AWS_SECRET_ACCESS_KEY", production=None)
AWS_STORAGE_BUCKET_NAME = from_env("AWS_STORAGE_BUCKET_NAME", production=None)
AWS_DEFAULT_ACL = "private"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_S3_SIGNATURE_VERSION = "s3v4"

if AWS_STORAGE_BUCKET_NAME is not None:
    DEFAULT_FILE_STORAGE = "thaliawebsite.storage.backend.PrivateS3Storage"
    PUBLIC_FILE_STORAGE = "thaliawebsite.storage.backend.PublicS3Storage"
    PUBLIC_MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.eu-west-1.amazonaws.com/"
else:
    DEFAULT_FILE_STORAGE = "thaliawebsite.storage.backend.PrivateFileSystemStorage"
    PUBLIC_FILE_STORAGE = "thaliawebsite.storage.backend.PublicFileSystemStorage"
    PUBLIC_MEDIA_URL = "/media/public/"

# https://docs.djangoproject.com/en/dev/ref/settings/#conn-max-age
CONN_MAX_AGE = int(from_env("CONN_MAX_AGE", development="0", production="60"))

# Useful for managing members
# https://docs.djangoproject.com/en/dev/ref/settings/#data-upload-max-number-fields
DATA_UPLOAD_MAX_NUMBER_FIELDS = os.environ.get("DATA_UPLOAD_MAX_NUMBER_FIELDS", 10000)

# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = setting(development=True, production=False, testing=False)

# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = setting(development=False, production=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = setting(development=False, production=True)

# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

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
    from firebase_admin import initialize_app, credentials

    try:
        initialize_app(credential=credentials.Certificate(FIREBASE_CREDENTIALS))
    except ValueError as e:
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
# Conscribo settings
CONSCRIBO_ACCOUNT = os.environ.get("CONSCRIBO_ACCOUNT", "")
CONSCRIBO_USER = os.environ.get("CONSCRIBO_USER", "")
CONSCRIBO_PASSWORD = os.environ.get("CONSCRIBO_PASSWORD", "")

###############################################################################
# Sentry setup
if "SENTRY_DSN" in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    # Pylint sees the faked init class that sentry uses for typing purposes
    # pylint: disable=abstract-class-instantiated
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        release=SOURCE_COMMIT,
        send_default_pii=True,
        environment=DJANGO_ENV,
        traces_sample_rate=0.2,
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
    "oauth2_provider",
    "corsheaders",
    "django_bootstrap5",
    "tinymce",
    "rest_framework",
    "rest_framework.authtoken",
    "compressor",
    "debug_toolbar",
    "admin_auto_filters",
    # Our apps
    # Directly link to the app config when applicable as recommended
    # by the docs: https://docs.djangoproject.com/en/2.0/ref/applications/
    "thaliawebsite.apps.ThaliaWebsiteConfig",  # include for admin settings
    # Load django.contrib.admin after thaliawebsite so the admin page gets modified
    "django.contrib.admin",
    "pushnotifications.apps.PushNotificationsConfig",
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
    "announcements.apps.AnnouncementsConfig",
    "registrations.apps.RegistrationsConfig",
    "payments.apps.PaymentsConfig",
    "singlepages.apps.SinglepagesConfig",
    "shortlinks.apps.ShortLinkConfig",
    "sales.apps.SalesConfig",
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
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # Our middleware
    "members.middleware.MemberMiddleware",
]

if DJANGO_ENV in ("development", "testing"):
    INSTALLED_APPS += ["django_template_check"]

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
                "thaliawebsite.context_processors.thumbnail_sizes",
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
        "formatters": {
            "verbose": {"format": "%(asctime)s %(name)s[%(levelname)s]: %(message)s"},
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            }
        },
        "loggers": {
            "django": {"handlers": [], "level": "INFO"},
            "": {"handlers": ["console"], "level": "INFO"},
        },
    }

WSGI_APPLICATION = "thaliawebsite.wsgi.application"

# Login pages
LOGIN_URL = "/user/login/"

LOGIN_REDIRECT_URL = "/"

# Cors configuration
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(?:api/v1|api/v2|user/oauth)/.*"

# OAuth configuration
OIDC_RSA_PRIVATE_KEY = from_env("OIDC_RSA_PRIVATE_KEY", testing=None)
if OIDC_RSA_PRIVATE_KEY is not None:
    OIDC_RSA_PRIVATE_KEY = base64.urlsafe_b64decode(OIDC_RSA_PRIVATE_KEY)

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
    "ALLOWED_VERSIONS": ["v1", "v2", "calendarjs"],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_SCHEMA_CLASS": "thaliawebsite.api.openapi.OAuthAutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "thaliawebsite.api.throttling.AnonRateThrottle",
        "thaliawebsite.api.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": setting(
        production={"anon": "30/min", "user": "30/min"},
        staging={"anon": "30/min", "user": "30/min"},
        development={"anon": None, "user": None},
    ),
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

DATETIME_FORMAT = "j M, Y, H:i"

LANGUAGE_CODE = "en"

TIME_ZONE = "Europe/Amsterdam"

USE_I18N = True

USE_L10N = False

USE_TZ = True

LANGUAGES = [("en", _("English"))]

LOCALE_PATHS = ("locale",)

# Static files
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # other finders
    "compressor.finders.CompressorFinder",
)

NORMAL_STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
MANIFEST_STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)
STATICFILES_STORAGE = setting(
    development=NORMAL_STATICFILES_STORAGE,
    production=MANIFEST_STATICFILES_STORAGE,
)

# Compressor settings
COMPRESS_ENABLED = True

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}

# Precompiler settings
STATIC_PRECOMPILER_LIST_FILES = True

# See utils/model/signals.py for explanation
SUSPEND_SIGNALS = False

THUMBNAIL_SIZES = {
    "small": "300x300",
    "medium": "600x600",
    "large": "1200x900",
    "avatar_large": "900x900",
    "slide_small": "500x108",
    "slide_medium": "1000x215",
    "slide": "2000x430",
}

# Photos settings
PHOTO_UPLOAD_SIZE = 2560, 1440

# TinyMCE config
TINYMCE_DEFAULT_CONFIG = {
    "max_height": 500,
    "menubar": False,
    "plugins": "autolink autoresize link image code media paste",
    "toolbar": "h2 h3 | bold italic underline strikethrough | image media | link unlink | "
    "bullist numlist | undo redo | code",
    "contextmenu": "bold italic underline strikethrough | link",
    "paste_as_text": True,
    "relative_urls": False,
    "remove_script_host": False,
    "autoresize_bottom_margin": 50,
}

BOOTSTRAP5 = {"required_css_class": "required-field"}

# https://docs.djangoproject.com/en/dev/ref/settings/#default-exception-reporter-filter
DEFAULT_EXCEPTION_REPORTER_FILTER = (
    "utils.exception_filter.ThaliaSafeExceptionReporterFilter"
)

# Make sure the locations in django.po files don't include line nrs.
makemessages.Command.xgettext_options.append("--add-location=file")
