"""
Settings for CI testing

This file is loaded by __init__.py if GITLAB_CI is set in the environment
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'thalia',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'postgres',
        'PORT': 5432,
    },
}
