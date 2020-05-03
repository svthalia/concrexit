"""
Django production settings for thaliawebsite project.

Many of these settings override settings from settings.py.

This file is loaded by __init__.py if the environment variable
`DJANGO_PRODUCTION` is set.

See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/
"""
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from . import settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG") == "True"

if "SITE_DOMAIN" in os.environ:
    ALLOWED_HOSTS = [os.environ.get("SITE_DOMAIN")]

# Database settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "NAME": os.environ.get("POSTGRES_DB"),
        "HOST": os.environ.get("DJANGO_POSTGRES_HOST"),
        "PORT": 5432,
    }
}

# Persistent database connections
CONN_MAX_AGE = "60"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# Where to store uploaded files
MEDIA_ROOT = "/concrexit/media"
MEDIA_URL = "/media/"  # Public is included by the db fields

if not settings.DEBUG:
    SENDFILE_BACKEND = "django_sendfile.backends.nginx"
SENDFILE_URL = "/media/sendfile/"
SENDFILE_ROOT = "/concrexit/media/"

STATIC_URL = "/static/"
STATIC_ROOT = "/concrexit/static"

if not DEBUG:
    COMPRESS_OFFLINE = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

if os.environ.get("DJANGO_SSLONLY"):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = False

# Use caching template loader
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "announcements.context_processors.announcements",
                "thaliawebsite.context_processors.source_commit",
                "thaliawebsite.context_processors.thumbnail_sizes",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
        },
    },
]

# ADMINS
ADMINS = [("Technicie", "www@thalia.nu")]

# Email backend
if os.environ.get("DJANGO_EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["DJANGO_EMAIL_HOST"]
    EMAIL_PORT = os.environ["DJANGO_EMAIL_PORT"]
    EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", False) == "True"
    EMAIL_USE_SSL = os.environ.get("DJANGO_EMAIL_USE_SSL", False) == "True"
    EMAIL_TIMEOUT = 10

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(name)s " "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "logfile": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": "/concrexit/log/django.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "logfile"],
            "level": "INFO",
            "propagate": False,
        },
        "": {"handlers": ["logfile"], "level": "INFO",},
    },
}

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    release=os.environ.get("SOURCE_COMMIT"),
    send_default_pii=True,
)
