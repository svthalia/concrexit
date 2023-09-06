import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FieldFile, ImageFieldFile

from thumbnails.backends.metadata import ImageMeta
from thumbnails.files import ThumbnailedImageFile
from thumbnails.images import Thumbnail
from thumbnails.models import ThumbnailMeta


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


def get_media_url(
    file,
    attachment=False,
    absolute_url: bool = False,
    expire_seconds: int = None,
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
    if isinstance(file, (ImageFieldFile, FieldFile, Thumbnail)):
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
    expire_seconds: int = None,
):
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


def fetch_thumbnails_db(images, sizes=None):
    """Prefetches thumbnails from the database in one query.

    :param images: A list of images to prefetch thumbnails for.
    :param sizes: A list of sizes to prefetch. If None, all sizes will be prefetched.
    :return: None
    """
    if not images:
        return

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
