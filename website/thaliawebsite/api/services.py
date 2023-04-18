from django.conf import settings

from utils.media.services import get_media_url, get_thumbnail_url


def create_image_thumbnail_dict(
    request,
    file,
    placeholder="",
    size_small="small",
    size_medium="medium",
    size_large="large",
):
    if file:
        return {
            "full": request.build_absolute_uri(get_media_url(file)),
            "small": request.build_absolute_uri(get_thumbnail_url(file, size_small)),
            "medium": request.build_absolute_uri(get_thumbnail_url(file, size_medium)),
            "large": request.build_absolute_uri(get_thumbnail_url(file, size_large)),
        }
    return {
        "full": placeholder,
        "small": placeholder,
        "medium": placeholder,
        "large": placeholder,
    }
