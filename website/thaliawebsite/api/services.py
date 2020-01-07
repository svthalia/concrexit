from django.conf import settings

from utils.media.services import get_media_url, get_thumbnail_url


def create_image_thumbnail_dict(
    request,
    file,
    placeholder="",
    size_small=settings.THUMBNAIL_SIZES["small"],
    size_medium=settings.THUMBNAIL_SIZES["medium"],
    size_large=settings.THUMBNAIL_SIZES["large"],
    fit_small=True,
    fit_medium=True,
    fit_large=True,
):
    if file:
        return {
            "full": request.build_absolute_uri(get_media_url(file)),
            "small": request.build_absolute_uri(
                get_thumbnail_url(file, size_small, fit=fit_small)
            ),
            "medium": request.build_absolute_uri(
                get_thumbnail_url(file, size_medium, fit=fit_medium)
            ),
            "large": request.build_absolute_uri(
                get_thumbnail_url(file, size_large, fit=fit_large)
            ),
        }
    return {
        "full": placeholder,
        "small": placeholder,
        "medium": placeholder,
        "large": placeholder,
    }
