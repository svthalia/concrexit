import io
import os

from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.conf import settings
from django.core import signing
from django.urls import reverse

from thaliawebsite.storage.backend import PublicMediaStorage, PrivateMediaStorage


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
    storage.save(path, file)

def get_media_url(path, attachment=False):
    """Get the url of the provided media file to serve in a browser.

    If the file is private a signature will be added.
    Do NOT use this with user input
    :param path: the location of the file
    :param attachment: True if the file is a forced download
    :return: the url of the media
    """
    if isinstance(path, ImageFieldFile):
        path = path.name
    if isinstance(path, FieldFile):
        path = path.name

    parts = path.split("/")
    query = ""
    url_path = path
    sig_info = {
        "visibility": "private" if parts[0] != "public" else "public",
        "serve_path": path,
        "attachment": attachment,
    }

    if sig_info["visibility"] == "private":
        # Add private to path and calculate signature
        url_path = f"private/{path}"
        query = f"?sig={signing.dumps(sig_info)}"
        return f"{settings.MEDIA_URL}{url_path}{query}"

    media_url = settings.MEDIA_URL if sig_info["visibility"] == 'private' else settings.PUBLIC_MEDIA_URL
    return f"{media_url}{url_path}{query}"


def get_thumbnail_url(file, size, fit=True):
    """Get the thumbnail url of a media file, NEVER use this with user input.

    If the thumbnail exists this function will return the url of the
    media file, with signature if necessary. Does it not yet exist a route
    that executes the :func:`utils.media.views.generate_thumbnail`
    will be the output.
    :param path: the location of the file
    :param size: size of the image
    :param fit: False to keep the aspect ratio, True to crop
    :return: direct media url or generate-thumbnail path
    """
    if not isinstance(file, ImageFieldFile) and not isinstance(file, FieldFile):
        raise NotImplementedError()

    storage = file.storage
    path = file.name

    query = ""
    size_fit = "{}_{}".format(size, int(fit))
    parts = path.split("/")

    if parts[-1].endswith(".svg") and parts[0] == "public":
        return f"{settings.MEDIA_URL}{path}"

    sig_info = {
        "size": size,
        "fit": int(fit),
        "path": path,
    }

    # Check if the image is public and assemble useful information
    if "PublicMediaStorage" in str(type(storage)):
        # TODO: Should not need to remove public, since migrations should remove that from the name
        sig_info["path"] = "/".join(parts[1:] if parts[0] == "public" else parts)
        sig_info["visibility"] = "public"
    else:
        sig_info["visibility"] = "private"

    sig_info["thumb_path"] = f'thumbnails/{size_fit}/{sig_info["path"]}'
    url_path = f'{sig_info["visibility"]}/thumbnails/' f'{size_fit}/{sig_info["path"]}'

    full_original_path = sig_info["path"]
    full_thumb_path = sig_info["thumb_path"]
    if sig_info["visibility"] == "public":
        full_original_path = os.path.join(
            "public", sig_info["path"]
        )
        full_thumb_path = os.path.join(
            "public", sig_info["thumb_path"]
        )

    sig_info["serve_path"] = full_thumb_path

    # Check if we need to generate, then redirect to the generating route,
    # otherwise just return the serving file path
    if not storage.exists(full_thumb_path) or (
        storage.exists(full_original_path)
        and storage.get_modified_time(full_original_path)
        > storage.get_modified_time(full_thumb_path)
    ):
        # Put all image info in signature for the generate view
        query = f"?sig={signing.dumps(sig_info)}"
        # We provide a URL instead of calling it as a function, so that using
        # it means kicking off a new GET request. If we would generate all
        # thumbnails inline, loading an album overview would have high latency.
        return (
            reverse(
                "generate-thumbnail", args=[os.path.join(size_fit, sig_info["path"])]
            )
            + query
        )

    if sig_info["visibility"] == "private":
        # Put all image info in signature for serve view
        query = f"?sig={signing.dumps(sig_info)}"


    media_url = settings.MEDIA_URL if sig_info["visibility"] == 'private' else settings.PUBLIC_MEDIA_URL
    return f"{media_url}{url_path}{query}"
