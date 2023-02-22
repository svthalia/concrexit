import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage, get_storage_class
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


def get_media_url(file, attachment=False):
    """Get the url of the provided media file to serve in a browser.

    If the file is private a signature will be added.
    Do NOT use this with user input
    :param file: the file field
    :param attachment: filename to use for the attachment or False to not download as attachment
    :return: the url of the media
    """
    storage = DefaultStorage()
    file_name = file
    if isinstance(file, (ImageFieldFile, FieldFile, Thumbnail)):
        storage = file.storage
        file_name = file.name

    return str(storage.url(file_name, attachment))


def get_thumbnail_url(file, size, fit=True):
    storage = DefaultStorage()
    name = file

    if isinstance(file, (ImageFieldFile, FieldFile)):
        storage = file.storage
        name = file.name

    is_public = isinstance(storage, get_storage_class(settings.PUBLIC_FILE_STORAGE))

    if name.endswith(".svg") and is_public:
        return storage.url(name)

    if isinstance(file, ThumbnailedImageFile):
        if size == "small":
            return get_media_url(file.thumbnails.small)
        if size == "medium":
            return get_media_url(file.thumbnails.medium)
        if size == "large":
            return get_media_url(file.thumbnails.large)

    return get_media_url(file)
