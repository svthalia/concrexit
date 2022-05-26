import io
import os

from django.conf import settings
from django.core import signing
from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class, DefaultStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.urls import reverse


def save_image(storage, image, path, format):
    buffer = io.BytesIO()
    image.convert("RGB").save(fp=buffer, format=format)
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
    :param attachment: True if the file is a forced download
    :return: the url of the media
    """
    storage = DefaultStorage()
    file_name = file
    if isinstance(file, ImageFieldFile) or isinstance(file, FieldFile):
        storage = file.storage
        file_name = file.name

    return f"{storage.url(file_name, attachment)}"


def get_thumbnail_url(file, size, fit=True):
    """Get the thumbnail url of a media file, NEVER use this with user input.

    If the thumbnail exists this function will return the url of the
    media file, with signature if necessary. Does it not yet exist a route
    that executes the :func:`utils.media.views.generate_thumbnail`
    will be the output.
    :param file: the file field
    :param size: size of the image
    :param fit: False to keep the aspect ratio, True to crop
    :return: direct media url or generate-thumbnail path
    """
    storage = DefaultStorage()
    name = file

    if isinstance(file, ImageFieldFile) or isinstance(file, FieldFile):
        storage = file.storage
        name = file.name

    is_public = isinstance(storage, get_storage_class(settings.PUBLIC_FILE_STORAGE))
    size_fit = "{}_{}".format(size, int(fit))

    if name.endswith(".svg") and is_public:
        return storage.url(name)

    sig_info = {
        "size": size,
        "fit": int(fit),
        "name": name,
        "thumb_path": f"thumbnails/{size_fit}/{name}",
        "serve_path": f"thumbnails/{size_fit}/{name}",
        "storage": f"{storage.__class__.__module__}.{storage.__class__.__name__}",
    }

    # Check if we need to generate, then redirect to the generating route,
    # otherwise just return the serving file path
    if not storage.exists(sig_info["thumb_path"]) or (
        storage.exists(name)
        and storage.get_modified_time(name)
        > storage.get_modified_time(sig_info["thumb_path"])
    ):
        # Put all image info in signature for the generate view
        query = f"?sig={signing.dumps(sig_info)}"
        # We provide a URL instead of calling it as a function, so that using
        # it means kicking off a new GET request. If we would generate all
        # thumbnails inline, loading an album overview would have high latency.
        return (
            reverse(
                "generate-thumbnail", args=[os.path.join(size_fit, sig_info["name"])]
            )
            + query
        )

    return storage.url(sig_info["serve_path"])
