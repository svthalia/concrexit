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

from django.core.management.commands import makemessages
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
INTERNAL_IPS = ['127.0.0.1']

if not DEBUG:  # Django 1.10.3 security release changed behaviour
    ALLOWED_HOSTS = []

SITE_ID = 1
BASE_URL = 'https://thalia.nu'

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
    'bootstrap4',
    'tinymce',
    'rest_framework',
    'rest_framework.authtoken',
    'compressor',
    'corsheaders',
    # Our apps
    # Directly link to the app config when applicable as recommended
    # by the docs: https://docs.djangoproject.com/en/2.0/ref/applications/
    'thaliawebsite',  # include for admin settings
    'pushnotifications.apps.PushNotificationsConfig',
    'members.apps.MembersConfig',
    'documents.apps.DocumentsConfig',
    'activemembers.apps.ActiveMembersConfig',
    'photos.apps.PhotosConfig',
    'utils',
    'mailinglists.apps.MailinglistsConfig',
    'merchandise.apps.MerchandiseConfig',
    'thabloid.apps.ThabloidConfig',
    'partners.apps.PartnersConfig',
    'events.apps.EventsConfig',
    'pizzas.apps.PizzasConfig',
    'newsletters.apps.NewslettersConfig',
    'education.apps.EducationConfig',
    'announcements.apps.AnnouncementsConfig',
    'registrations.apps.RegistrationsConfig',
    'payments.apps.PaymentsConfig',
]

# enable template check if it's installed
# this allows us to not have it enabled in production
try:
    import django_template_check
    del django_template_check
    INSTALLED_APPS.append('django_template_check')
except ImportError:
    pass

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
    # Our middleware
    'members.middleware.MemberMiddleware',
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
                'thaliawebsite.context_processors.source_commit',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'announcements.context_processors.announcements',
                'thaliawebsite.context_processors.thumbnail_sizes',
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
    'activemembers.backends.MemberGroupBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_VERSIONING_CLASS':
        'rest_framework.versioning.URLPathVersioning',
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en'

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

# Membership prices
MEMBERSHIP_PRICES = {
    'year': 7.5,
    'study': 30,
}

THUMBNAIL_SIZES = {
    'small': '150x150',
    'medium': '300x300',
    'large': '1024x768',
    'slide': '2000x430'
}

# Placeholder Firebase config
FIREBASE_CREDENTIALS = {}

# Default FROM email
DEFAULT_FROM_EMAIL = 'noreply@thalia.nu'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Newsletter settings
NEWSLETTER_FROM_ADDRESS = 'nieuwsbrief@thalia.nu'

# Website FROM address
WEBSITE_FROM_ADDRESS = 'noreply@thalia.nu'

# Board notification address
BOARD_NOTIFICATION_ADDRESS = 'info@thalia.nu'

# Partners notification email
PARTNER_EMAIL = "samenwerking@thalia.nu"

# Mailinglist API key
MAILINGLIST_API_SECRET = ''

# Members Sentry API key
MEMBERS_SENTRY_API_SECRET = ''

# Activemembers NextCloud API key
ACTIVEMEMBERS_NEXTCLOUD_API_SECRET = ''

# Google maps API key and secrets
GOOGLE_MAPS_API_KEY = ''
GOOGLE_MAPS_API_SECRET = ''

# Photos settings
PHOTO_UPLOAD_SIZE = 1920, 1080

# API key for wiki
WIKI_API_KEY = 'debug'

# CORS config
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'^/api/.*$'
CORS_ALLOW_METHODS = ('GET', 'POST')

# TinyMCE config
TINYMCE_JS_URL = '/static/tinymce/js/tinymce/tinymce.min.js'

TINYMCE_DEFAULT_CONFIG = {
    'selector': 'textarea',
    'theme': 'modern',
    'plugins': 'link image paste code contextmenu',
    'toolbar1': 'bold italic underline strikethrough | link unlink | '
                'bullist numlist | undo redo | code',
    'contextmenu': 'bold italic underline strikethrough | image',
    'menubar': False,
    'inline': False,
    'statusbar': True,
    'width': 'auto',
    'height': 240,
    'paste_as_text': True,
    'relative_urls': False,
    'remove_script_host': False,
}


DEFAULT_EXCEPTION_REPORTER_FILTER = (
    'utils.exception_filter.ThaliaSafeExceptionReporterFilter')


# Make sure the locations in django.po files don't include line nrs.
makemessages.Command.xgettext_options.append('--add-location=file')
