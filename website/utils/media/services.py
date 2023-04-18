import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FieldFile, ImageFieldFile

from thumbnails.files import ThumbnailedImageFile
from thumbnails.images import Thumbnail


def save_image(storage, image, path, format):
    buffer = io.BytesIO()
    image.convert("RGB" if format == "JPEG" else "RGBA").save(fp=buffer, format=format)
    buff_val = buffer.getvalue()
    content = ContentFile(buff_val)
    file = InMemoryUploadedFile(
        content,
        None,
        f"foo.{format.lower()}",
        f"image/{format.lower()}",
        content.tell,
        None,
    )
    return storage.save(path, file)


def get_media_url(file, attachment: bool | str = False, absolute_url: bool = False):
    """Get the url of the provided media file to serve in a browser.

    If the file is private a signature will be added.
    Do NOT use this with user input
    :param file: The file field or path.
    :param attachment: Filename to use for the attachment or False to not download as attachment.
    :param absolute_url: True if we want the full url including the scheme and domain.
    :return: The url of the media.
    """
    storage = DefaultStorage()
    file_name = file
    if isinstance(file, (ImageFieldFile, FieldFile, Thumbnail)):
        storage = file.storage
        file_name = file.name

    url = storage.url(file_name, attachment)

    # If the url is not absolute, but we want an absolute url, add the base url.
    if absolute_url and not url.startswith(("http://", "https://")):
        url = f"{settings.BASE_URL}{url}"

    return url


def get_thumbnail_url(file, size: str, absolute_url: bool = False):
    name = file
    if isinstance(file, (ImageFieldFile, FieldFile)):
        name = file.name

    if isinstance(file, ThumbnailedImageFile):
        if not name.endswith(".svg"):
            if size in settings.THUMBNAIL_SIZES:
                return get_media_url(
                    getattr(file.thumbnails, size),
                    absolute_url=absolute_url,
                )

    return get_media_url(file, absolute_url=absolute_url)
