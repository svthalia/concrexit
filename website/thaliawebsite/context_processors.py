"""These context processors can be used to expand the context provided to views."""
from django.conf import settings


def source_commit(_):
    """Get the SOURCE_COMMIT environment variable."""
    return {"SOURCE_COMMIT": settings.SOURCE_COMMIT}


def thumbnail_sizes(_):
    """Get the defined sizes for thumbnails."""
    return {
        "THUMBNAIL_SIZE_SMALL": settings.THUMBNAIL_SIZES["small"],
        "THUMBNAIL_SIZE_MEDIUM": settings.THUMBNAIL_SIZES["medium"],
        "THUMBNAIL_SIZE_LARGE": settings.THUMBNAIL_SIZES["large"],
    }
