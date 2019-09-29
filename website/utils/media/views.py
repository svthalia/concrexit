"""Utility views"""
import os
from datetime import timedelta

from PIL import Image, ImageOps
from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.core.signing import BadSignature
from django.http import Http404
from django.shortcuts import redirect
from sendfile import sendfile


def _get_signature_info(request):
    if 'sig' in request.GET:
        signature = request.GET.get('sig')
        try:
            return signing.loads(signature, max_age=timedelta(hours=3))
        except BadSignature:
            pass
    raise PermissionDenied


def private_media(request, request_path):
    """
    Serve private media files
    :param request: the request
    :return: the media file
    """
    # Get image information from signature
    # raises PermissionDenied if bad signature
    info = _get_signature_info(request)

    if (not os.path.isfile(info['serve_path'])
            or not info['serve_path'].endswith(request_path)):
        # 404 if the file does not exist
        raise Http404("Media not found.")

    # Serve the file
    return sendfile(request, info['serve_path'],
                    attachment=info.get('attachment', False))


def generate_thumbnail(request, request_path):
    """
    Generate thumbnail and redirect user to new location

    The thumbnails are generated with this route. Because the
    thumbnails will be generated in parallel, it will not block
    page load when many thumbnails need to be generated.
    After it is done, the user is redirected to the new location
    of the thumbnail.

    :param HttpRequest request: the request
    :return: HTTP Redirect to thumbnail
    """
    # Get image information from signature
    # raises PermissionDenied if bad signature
    query = ''
    sig_info = _get_signature_info(request)

    if not sig_info['thumb_path'].endswith(request_path):
        # 404 if the file does not exist
        raise Http404("Media not found.")

    if sig_info['visibility'] == 'public':
        full_original_path = os.path.join(
            settings.MEDIA_ROOT, 'public', sig_info['path'])
        full_thumb_path = os.path.join(
            settings.MEDIA_ROOT, 'public', sig_info['thumb_path'])
    else:
        full_original_path = os.path.join(
            settings.MEDIA_ROOT, sig_info['path'])
        full_thumb_path = os.path.join(
            settings.MEDIA_ROOT, sig_info['thumb_path'])

    if not os.path.exists(full_original_path):
        raise Http404

    # Check if directory for thumbnail exists, if not create it
    os.makedirs(os.path.dirname(full_thumb_path), exist_ok=True)
    # Skip generating the thumbnail if it exists
    if (not os.path.isfile(full_thumb_path) or
            os.path.getmtime(full_original_path)
            > os.path.getmtime(full_thumb_path)):
        # Create a thumbnail from the original_path, saved to thumb_path
        image = Image.open(full_original_path)
        size = tuple(int(dim) for dim in sig_info['size'].split('x'))
        if not sig_info['fit']:
            ratio = min([a / b for a, b in zip(size, image.size)])
            size = tuple(int(ratio * x) for x in image.size)

        if size[0] == image.size[0] and size[1] == image.size[1]:
            image.save(full_thumb_path)
        else:
            thumb = ImageOps.fit(image, size, Image.ANTIALIAS)
            thumb.save(full_thumb_path)

    if sig_info['visibility'] == 'private':
        query = f'?sig={request.GET["sig"]}'

    # Redirect to the serving url of the image
    # for public images this goes via a static file server (i.e. nginx)
    # for private images this is a call to private_media
    return redirect(f'{settings.MEDIA_URL}'
                    f'{sig_info["visibility"]}/thumbnails/'
                    f'{sig_info["size"]}_{sig_info["fit"]}/'
                    f'{sig_info["path"]}{query}',
                    permanent=True)
