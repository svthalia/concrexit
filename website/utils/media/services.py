import os
from functools import partial
from secrets import token_hex

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.db.models.fields.files import FieldFile, ImageFieldFile

from thumbnails.backends.metadata import ImageMeta
from thumbnails.fields import fetch_thumbnails as fetch_thumbnails_redis
from thumbnails.files import ThumbnailedImageFile
from thumbnails.images import Thumbnail
from thumbnails.models import ThumbnailMeta


def _generic_upload_to(instance, filename, prefix: str, token_bytes: int):
    ext = os.path.splitext(filename)[1]
    return os.path.join(prefix, f"{token_hex(token_bytes)}{ext}")


def get_upload_to_function(prefix: str, token_bytes: int = 8):
    """Return a partial function that can be used as the upload_to argument of a FileField.

    This is useful to avoid having numerous functions that all do the same thing, with
    different prefixes. Using a partial function makes it serializable for migrations.
    See: https://docs.djangoproject.com/en/4.2/topics/migrations/#migration-serializing.

    The resulting function returns paths like `<prefix>/<random hex string>.<ext>`.
    """
    return partial(_generic_upload_to, prefix=prefix, token_bytes=token_bytes)


def get_media_url(
    file,
    attachment=False,
    absolute_url: bool = False,
    expire_seconds: int | None = None,
):
    """Get the url of the provided media file to serve in a browser.

    If the file is private a signature will be added.
    Do NOT use this with user input
    :param file: The file field or path.
    :param attachment: Filename to use for the attachment or False to not download as attachment.
    :param absolute_url: True if we want the full url including the scheme and domain.
    :param expire_seconds: The number of seconds the url should be valid for if on S3.
    :return: The url of the media.
    """
    storage = DefaultStorage()
    file_name = file
    if isinstance(file, ImageFieldFile | FieldFile | Thumbnail):
        storage = file.storage
        file_name = file.name

    url = storage.url(file_name, attachment, expire_seconds)

    # If the url is not absolute, but we want an absolute url, add the base url.
    if absolute_url and not url.startswith(("http://", "https://")):
        url = f"{settings.BASE_URL}{url}"

    return url


def get_thumbnail_url(
    file,
    size: str,
    absolute_url: bool = False,
    expire_seconds: int | None = None,
):
    name = file
    if isinstance(file, ImageFieldFile | FieldFile):
        name = file.name

    if isinstance(file, ThumbnailedImageFile):
        if not name.endswith(".svg"):
            if size in settings.THUMBNAIL_SIZES:
                return get_media_url(
                    getattr(file.thumbnails, size),
                    absolute_url=absolute_url,
                )

    return get_media_url(file, absolute_url=absolute_url)


def fetch_thumbnails(images: list, sizes=None):
    """Prefetches thumbnails from the database or redis efficiently.

    :param images: A list of images to prefetch thumbnails for.
    :param sizes: A list of sizes to prefetch. If None, all sizes will be prefetched.
    :return: None
    """
    # Filter out empty ImageFieldFiles.
    images = list(filter(bool, images))

    if not images:
        return

    if (
        settings.THUMBNAILS["METADATA"]["BACKEND"]
        != "thumbnails.backends.metadata.DatabaseBackend"
    ):
        return fetch_thumbnails_redis(images, sizes)

    image_dict = {image.thumbnails.source_image.name: image for image in images}
    thumbnails = ThumbnailMeta.objects.select_related("source").filter(
        source__name__in=image_dict.keys()
    )
    if sizes:
        thumbnails.filter(size__in=sizes)

    for source_name, thumb_name, thumb_size in thumbnails.values_list(
        "source__name", "name", "size"
    ):
        thumbnails = image_dict[source_name].thumbnails
        if not thumbnails._thumbnails:
            thumbnails._thumbnails = {}
        image_meta = ImageMeta(source_name, thumb_name, thumb_size)
        thumbnails._thumbnails[thumb_size] = Thumbnail(
            image_meta, storage=thumbnails.storage
        )
