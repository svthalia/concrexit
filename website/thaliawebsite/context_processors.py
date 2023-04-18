"""These context processors can be used to expand the context provided to views."""
from django.conf import settings
from django.utils import timezone


def source_commit(_):
    """Get the SOURCE_COMMIT environment variable."""
    return {"SOURCE_COMMIT": settings.SOURCE_COMMIT}


def thumbnail_sizes(_):
    """Get the defined sizes for thumbnails."""
    return {
        "THUMBNAIL_SIZE_SMALL": "small",
        "THUMBNAIL_SIZE_MEDIUM": "medium",
        "THUMBNAIL_SIZE_LARGE": "large",
    }


def aprilfools(_):
    now = timezone.now()
    return {"APRIL_FOOLS": now.month == 4 and now.day == 1}


def lustrum_styling(_):
    return {
        "lustrumstyling": timezone.datetime(2022, 4, 22).date()
        <= timezone.now().date()
        <= timezone.datetime(2022, 4, 29).date()
    }
