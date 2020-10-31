"""
These context processors can be used to expand the context provided
tos views.
"""
import os
from django.conf import settings
from django.utils import timezone


def source_commit(_):
    """Get the SOURCE_COMMIT environment variable"""
    return {"SOURCE_COMMIT": os.environ.get("SOURCE_COMMIT", "unknown")}


def thumbnail_sizes(_):
    """Get the defined sizes for thumbnails"""
    return {
        "THUMBNAIL_SIZE_SMALL": settings.THUMBNAIL_SIZES["small"],
        "THUMBNAIL_SIZE_MEDIUM": settings.THUMBNAIL_SIZES["medium"],
        "THUMBNAIL_SIZE_LARGE": settings.THUMBNAIL_SIZES["large"],
    }


def lustrum_styling(_):
    """Should the website be styled in lustrum styling"""
    return {
        "lustrumstyling": timezone.now().date() == timezone.datetime(2020, 11, 7).date()
        or settings.LUSTRUM_STYLING
    }
