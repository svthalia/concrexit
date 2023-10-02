"""The main module for the Thalia website.

This module defines settings and the URI layout.
We also handle some site-wide API stuff here.
"""

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import celery_app

__all__ = ("celery_app",)
