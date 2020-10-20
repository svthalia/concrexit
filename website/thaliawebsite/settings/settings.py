"""
Django settings for thaliawebsite project.

This file is loaded by __init__.py.

Its settings may be overridden by files loaded after it.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
import base64
import json
import os

from django.core.management.commands import makemessages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "#o-0d1q5&^&06tn@8pr1f(n3$crafd++^%sacao7hj*ea@c)^t"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS = ["*"]

if not DEBUG:  # Django 1.10.3 security release changed behaviour
    ALLOWED_HOSTS = ["*"]

SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "thalia.localhost")
BASE_URL = f"https://{SITE_DOMAIN}"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # Useful for managing members

# Application definition

# Load django.contrib.admin after thaliawebsite so the admin page gets modified
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
    "bootstrap4",
    "tinymce",
    "rest_framework",
    "rest_framework.authtoken",
    "compressor",
    # Our apps
    # Directly link to the app config when applicable as recommended
    # by the docs: https://docs.djangoproject.com/en/2.0/ref/applications/
    "thaliawebsite",  # include for admin settings
    "django.contrib.admin",
    "pushnotifications.apps.PushNotificationsConfig",
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
]

# enable template check if it's installed
# this allows us to not have it enabled in production
try:
    import django_template_check

    del django_template_check
    INSTALLED_APPS.append("django_template_check")
except ImportError:
    pass

MIDDLEWARE = [
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

ROOT_URLCONF = "thaliawebsite.urls"

# WARNING
# Also update this in production.py!!!
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
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
            ],
        },
    },
]

WSGI_APPLICATION = "thaliawebsite.wsgi.application"

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Login pages

LOGIN_URL = "/user/login/"

LOGIN_REDIRECT_URL = "/"

# Cors configuration
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(?:api|user/oauth)/.*"

# OAuth configuration
OAUTH2_PROVIDER = {
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https"] if not DEBUG else ["http", "https"],
    "SCOPES": {
        "read": "Authenticated read access to the website",
        "write": "Authenticated write access to the website",
        "members:read": "Read access to your member profile",
        "activemembers:read": "Read access to committee, society and board groups",
    },
}

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth."
            "password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {"NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),},
    {"NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),},
    {"NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),},
]

# allow to use md5 in tests
PASSWORD_HASHERS = (
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.MD5PasswordHasher",
)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "activemembers.backends.MemberGroupBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = "Europe/Amsterdam"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = [("en", _("English"))]

LOCALE_PATHS = ("locale",)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# Where to store uploaded files
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"  # Public is included by the db fields

SENDFILE_BACKEND = "django_sendfile.backends.development"

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # other finders
    "compressor.finders.CompressorFinder",
)

# Compressor settings
COMPRESS_ENABLED = True

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ]
}

# Precompiler settings
STATIC_PRECOMPILER_LIST_FILES = True

# See utils/model/signals.py for explanation
SUSPEND_SIGNALS = False

# Membership prices
MEMBERSHIP_PRICES = {
    "year": 7.5,
    "study": 30,
}

# Window during which a payment can be deleted again
PAYMENT_CHANGE_WINDOW = int(os.environ.get("PAYMENTS_CHANGE_WINDOW", 10 * 60))

THUMBNAIL_SIZES = {
    "small": "150x150",
    "medium": "300x300",
    "large": "1024x768",
    "slide": "2000x430",
}

# Firebase config
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "{}")
if FIREBASE_CREDENTIALS != "{}":
    FIREBASE_CREDENTIALS = base64.urlsafe_b64decode(FIREBASE_CREDENTIALS)
FIREBASE_CREDENTIALS = json.loads(FIREBASE_CREDENTIALS)

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
GSUITE_DOMAIN = os.environ.get("GSUITE_DOMAIN", "thalia.localhost")
GSUITE_MEMBERS_DOMAIN = os.environ.get(
    "GSUITE_MEMBERS_DOMAIN", "members.thalia.localhost"
)
GSUITE_MEMBERS_AUTOSYNC = os.environ.get("GSUITE_MEMBERS_AUTOSYNC", False) == "True"

EMAIL_DOMAIN_BLACKLIST = [GSUITE_MEMBERS_DOMAIN]

# Default FROM email
DEFAULT_FROM_EMAIL = f"noreply@{SITE_DOMAIN}"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Newsletter settings
NEWSLETTER_FROM_ADDRESS = f"newsletter@{SITE_DOMAIN}"

# Board notification address
BOARD_NOTIFICATION_ADDRESS = f"info@{SITE_DOMAIN}"

# Partners notification email
PARTNER_NOTIFICATION_ADDRESS = f"samenwerking@{SITE_DOMAIN}"

# Conscribo settings
CONSCRIBO_ACCOUNT = os.environ.get("CONSCRIBO_ACCOUNT", "")
CONSCRIBO_USER = os.environ.get("CONSCRIBO_USER", "")
CONSCRIBO_PASSWORD = os.environ.get("CONSCRIBO_PASSWORD", "")

# Payments creditor identifier
SEPA_CREDITOR_ID = os.environ.get("SEPA_CREDITOR_ID", "PLACEHOLDER")

# Payment batch withdrawal date default offset after creation date
PAYMENT_BATCH_DEFAULT_WITHDRAWAL_DATE_OFFSET = timezone.timedelta(days=14)

# Payment settings
THALIA_PAY_ENABLED_PAYMENT_METHOD = (
    os.environ.get("THALIA_PAY_ENABLED", "False") == "True"
)
THALIA_PAY_FOR_NEW_MEMBERS = (
    os.environ.get("THALIA_PAY_FOR_NEW_MEMBERS", "True") == "True"
)

# Google maps API key and secrets
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
GOOGLE_MAPS_API_SECRET = os.environ.get("GOOGLE_MAPS_API_SECRET", "")
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

# Photos settings
PHOTO_UPLOAD_SIZE = 2560, 1440

# TinyMCE config
TINYMCE_JS_URL = "/static/tinymce/js/tinymce/tinymce.min.js"

TINYMCE_DEFAULT_CONFIG = {
    "selector": "textarea",
    "theme": "modern",
    "plugins": "link image paste code contextmenu",
    "toolbar1": "bold italic underline strikethrough | link unlink | "
    "bullist numlist | undo redo | code",
    "contextmenu": "bold italic underline strikethrough | image",
    "menubar": False,
    "inline": False,
    "statusbar": True,
    "width": "auto",
    "height": 240,
    "paste_as_text": True,
    "relative_urls": False,
    "remove_script_host": False,
}

BOOTSTRAP4 = {"required_css_class": "required-field"}


DEFAULT_EXCEPTION_REPORTER_FILTER = (
    "utils.exception_filter.ThaliaSafeExceptionReporterFilter"
)


# Make sure the locations in django.po files don't include line nrs.
makemessages.Command.xgettext_options.append("--add-location=file")
