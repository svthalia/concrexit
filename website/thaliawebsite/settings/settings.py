"""
Django settings for thaliawebsite project.

This file is loaded by __init__.py.

Its settings may be overridden by files loaded after it.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os

from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#o-0d1q5&^&06tn@8pr1f(n3$crafd++^%sacao7hj*ea@c)^t'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if not DEBUG:  # Django 1.10.3 security release changed behaviour
    ALLOWED_HOSTS = []

SITE_ID = 1

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # Useful for managing members

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    # Dependencies
    'tinymce',
    'django_template_check',  # This is only necessary in development
    'rest_framework',
    'rest_framework.authtoken',
    'compressor',
    'corsheaders',
    # Our apps
    'thaliawebsite',  # include for admin settings
    'members',
    'documents',
    'activemembers',
    'photos',
    'utils',
    'mailinglists',
    'merchandise',
    'thabloid',
    'partners',
    'events',
    'pizzas',
    'newsletters',
    'education',
    'thaliapp',
    'announcements',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'thaliawebsite.urls'

# WARNING
# Also update this in production.py!!!
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
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
        },
    },
]

WSGI_APPLICATION = 'thaliawebsite.wsgi.application'

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Login pages

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.'
                 'password_validation.UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.'
                 'password_validation.MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.'
                 'password_validation.CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.'
                 'password_validation.NumericPasswordValidator'),
    },
]

# allow to use md5 in tests
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'activemembers.backends.CommitteeBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'nl'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('nl', _('Dutch'))
]

LOCALE_PATHS = ('locale',)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# Where to store uploaded files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'  # Public is included by the db fields

SENDFILE_BACKEND = 'sendfile.backends.development'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders
    'compressor.finders.CompressorFinder',
)

# Compressor settings
COMPRESS_ENABLED = True

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter',
                        'compressor.filters.cssmin.rCSSMinFilter']

# Precompiler settings
STATIC_PRECOMPILER_LIST_FILES = True

# Default FROM email
DEFAULT_FROM_EMAIL = 'noreply@thalia.nu'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Newsletter settings
NEWSLETTER_FROM_ADDRESS = 'nieuwsbrief@thalia.nu'

# Photos settings
PHOTO_UPLOAD_SIZE = 1920, 1080

# API key for wiki
WIKI_API_KEY = 'debug'
# API key for thaliapp related stuff
# SHA256 hash so it does not need replacement in production
THALIAPP_API_KEY = ('5b2bff55b74f74678dd578f8f669e959'
                    '09f356aa05548ecdf418e678af334844')

# CORS config
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'^/api/.*$'
CORS_ALLOW_METHODS = ('GET', 'POST')

# TinyMCE config
TINYMCE_DEFAULT_CONFIG = {
    'theme': "advanced",
    'theme_advanced_buttons1': "bold,italic,underline,separator," +
                               "link,unlink,separator,bullist," +
                               "numlist,separator,undo,redo",
    'theme_advanced_toolbar_location': "top",
    'relative_urls': False,
    'remove_script_host': False,
    'convert_urls': True,
    'plugins': "paste",
    'paste_auto_cleanup_on_paste': True,
    'paste_remove_styles': True,
    'paste_remove_styles_if_webkit': True,
    'paste_strip_class_attributes': "all",
}
