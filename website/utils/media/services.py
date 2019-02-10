import os

from django.db.models.fields.files import ImageFieldFile
from django.conf import settings
from django.core import signing
from django.urls import reverse


def get_media_url(path, attachment=False):
    """
    Get the url of the provided media file to serve in a browser.
    If the file is private a signature will be added.
    Do NOT use this with user input
    :param path: the location of the file
    :param attachment: True if the file is a forced download
    :return: the url of the media
    """
    if isinstance(path, ImageFieldFile):
        path = path.name

    parts = path.split('/')
    query = ''
    url_path = path
    sig_info = {
        'visibility': 'private' if parts[0] != 'public' else 'public',
        'serve_path': os.path.join(settings.MEDIA_ROOT, path),
        'attachment': attachment
    }

    if sig_info['visibility'] == 'private':
        # Add private to path and calculate signature
        url_path = f'private/{path}'
        query = f'?sig={signing.dumps(sig_info)}'

    return f'{settings.MEDIA_URL}{url_path}{query}'


def get_thumbnail_url(path, size, fit=True):
    """
    Get the thumbnail url of a media file. NEVER use this with user input.
    If the thumbnail exists this function will return the url of the
    media file, with signature if necessary. Does it not yet exist a route
    that executes the :func:`utils.media.views.generate_thumbnail`
    will be the output.
    :param path: the location of the file
    :param size: size of the image
    :param fit: False to keep the aspect ratio, True to crop
    :return: direct media url or generate-thumbnail path
    """
    if isinstance(path, ImageFieldFile):
        path = path.name

    query = ''
    size_fit = '{}_{}'.format(size, int(fit))
    parts = path.split('/')

    sig_info = {
        'size': size,
        'fit': int(fit),
        'path': path,
    }

    # Check if the image is public and assemble useful information
    if parts[0] == 'public':
        sig_info['path'] = '/'.join(parts[1:])
        sig_info['visibility'] = 'public'
    else:
        sig_info['visibility'] = 'private'

    sig_info['thumb_path'] = f'thumbnails/{size_fit}/{sig_info["path"]}'
    url_path = (f'{sig_info["visibility"]}/thumbnails/'
                f'{size_fit}/{sig_info["path"]}')

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

    sig_info['serve_path'] = full_thumb_path

    # Check if we need to generate, then redirect to the generating route,
    # otherwise just return the serving file path
    if (not os.path.isfile(full_thumb_path) or
        os.path.getmtime(full_original_path)
            > os.path.getmtime(full_thumb_path)):
        # Put all image info in signature for the generate view
        query = f'?sig={signing.dumps(sig_info)}'
        # We provide a URL instead of calling it as a function, so that using
        # it means kicking off a new GET request. If we would generate all
        # thumbnails inline, loading an album overview would have high latency.
        return reverse('generate-thumbnail',
                       args=[sig_info['visibility'],
                             os.path.join(size_fit, sig_info["path"])]) + query

    if sig_info['visibility'] == 'private':
        # Put all image info in signature for serve view
        query = f'?sig={signing.dumps(sig_info)}'

    return f'{settings.MEDIA_URL}{url_path}{query}'
