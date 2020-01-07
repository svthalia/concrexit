"""
Settings for CI testing

This file is loaded by __init__.py if GITLAB_CI is set in the environment
"""

import logging

from .settings import MIDDLEWARE

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "thalia",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "postgres",
        "PORT": 5432,
    },
}


# This won't help anyway
DEBUG = False
logging.disable(logging.CRITICAL)

# Fasters hashing
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# Strip unneeded middlewares
_ = [
    MIDDLEWARE.remove(x)
    for x in (
        "django.middleware.http.ConditionalGetMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
    )
]
