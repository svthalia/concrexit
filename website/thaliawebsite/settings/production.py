"""
Django settings for thaliawebsite project.

Docker version
"""

import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET',
    '#o-0d1q5&^&06tn@8pr1f(n3$crafd++^%sacao7hj*ea@c)^t')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_HOSTS', '').split(',')

ROOT_URLCONF = 'thaliawebsite.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_USER'),
        'USER': 'postgres',
        'DATABASE': os.environ.get('POSTGRES_DB'),
        'HOST': os.environ.get('DJANGO_POSTGRES_HOST'),
        'PORT': 5432,
    }
}
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# Where to store uploaded files
MEDIA_ROOT = os.path.join('/', 'media')
MEDIA_URL = '/media/'  # Public is included by the db fields

SENDFILE_BACKEND = 'sendfile.backends.development'

STATIC_URL = '/static/'
STATIC_ROOT = '/static'

COMPRESS_ENABLED = True

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'sass --scss {infile} {outfile}'),
)

COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter',
                        'compressor.filters.cssmin.rCSSMinFilter']

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

WIKI_API_KEY = os.environ.get('WIKI_API_KEY', 'changeme')
