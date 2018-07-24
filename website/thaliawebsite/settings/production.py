"""
Django production settings for thaliawebsite project.

Many of these settings override settings from settings.py.

This file is loaded by __init__.py if the environment variable
`DJANGO_PRODUCTION` is set.

See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/
"""

import os

from . import settings

INSTALLED_APPS = settings.INSTALLED_APPS
INSTALLED_APPS.append('raven.contrib.django.raven_compat')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET',
    '#o-0d1q5&^&06tn@8pr1f(n3$crafd++^%sacao7hj*ea@c)^t')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG') == 'True'

if 'DJANGO_HOSTS' in os.environ:
    ALLOWED_HOSTS = os.environ.get('DJANGO_HOSTS').split(',')

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'NAME': os.environ.get('POSTGRES_DB'),
        'HOST': os.environ.get('DJANGO_POSTGRES_HOST'),
        'PORT': 5432,
    }
}

# Persistent database connections
CONN_MAX_AGE = '60'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# Where to store uploaded files
MEDIA_ROOT = '/concrexit/media'
MEDIA_URL = '/media/'  # Public is included by the db fields

if not settings.DEBUG:
    SENDFILE_BACKEND = 'sendfile.backends.nginx'
SENDFILE_URL = '/media/'
SENDFILE_ROOT = '/concrexit/media/'

STATIC_URL = '/static/'
STATIC_ROOT = '/concrexit/static'

if not DEBUG:
    COMPRESS_OFFLINE = True

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

WIKI_API_KEY = os.environ.get('WIKI_API_KEY', 'changeme')
MIGRATION_KEY = os.environ.get('MIGRATION_KEY')
PUSH_NOTIFICATIONS_API_KEY = os.environ.get('PUSH_NOTIFICATIONS_API_KEY', '')
MAILINGLIST_API_SECRET = os.environ.get('MAILINGLIST_API_SECRET', '')

if os.environ.get('DJANGO_SSLONLY'):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Use caching template loader
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'partners.context_processors.showcased_partners',
                'announcements.context_processors.announcements',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

# ADMINS
ADMINS = [('Technicie', 'www@thalia.nu')]

# Email backend
if os.environ.get('DJANGO_EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ['DJANGO_EMAIL_HOST']
    EMAIL_PORT = os.environ['DJANGO_EMAIL_PORT']
    EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = os.environ.get('DJANGO_EMAIL_USE_TLS', False) == 'True'
    EMAIL_USE_SSL = os.environ.get('DJANGO_EMAIL_USE_SSL', False) == 'True'
    EMAIL_TIMEOUT = 10

# Secure headers
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'sentry': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'raven.contrib.django.raven_compat.'
                     'handlers.SentryHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}


RAVEN_CONFIG = {
    'dsn': os.environ.get('SENTRY_DSN'),
    'release': os.environ.get('SOURCE_COMMIT'),
}
