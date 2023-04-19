from utils.media.services import get_media_url, get_thumbnail_url


def create_image_thumbnail_dict(
    file,
    placeholder="",
    size_small="small",
    size_medium="medium",
    size_large="large",
):
    if file:
        return {
            "full": get_media_url(file, absolute_url=True),
            "small": get_thumbnail_url(file, size_small, absolute_url=True),
            "medium": get_thumbnail_url(file, size_medium, absolute_url=True),
            "large": get_thumbnail_url(file, size_large, absolute_url=True),
        }
    return {
        "full": placeholder,
        "small": placeholder,
        "medium": placeholder,
        "large": placeholder,
    }
