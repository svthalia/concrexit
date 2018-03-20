"""Thumbnail template tags"""
import os

from django import template
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from django.urls import reverse
from django.utils.http import urlquote

register = template.Library()  # pylint: disable=invalid-name


@register.simple_tag
def thumbnail(path, size, fit=True, api=False):
    """
    Get the thumbnail path for the specified image path.

    :param path: the path or image file to generate the thumb for
    :type path: ImageFieldFile or str
    :return: the path to the associated thumbnail
    :rtype: str
    """
    if isinstance(path, ImageFieldFile):
        path = path.name

    size_fit = '{}_{}'.format(size, int(fit))
    parts = path.split('/')

    if parts[0] == 'public':
        thumbpath = os.path.join(parts[0], 'thumbnails', size_fit, *parts[1:])
    else:
        thumbpath = os.path.join('thumbnails', size_fit, path)

    full_thumbpath = os.path.join(settings.MEDIA_ROOT, thumbpath)
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    # Check if we need to generate, then redirect to the generating route,
    # otherwise just return the file path
    if (not os.path.isfile(full_thumbpath) or
            os.path.getmtime(full_path) > os.path.getmtime(full_thumbpath)):
        pathuri = urlquote(path, safe='')
        thumburi = urlquote(thumbpath, safe='')
        # We provide a URL instead of calling it as a function, so that using
        # it means kicking off a new GET request. If we would generate all
        # thumbnails inline, loading an album overview would have high latency.
        if api:
            return reverse('generate-thumbnail-api',
                           args=[size_fit, pathuri, thumburi])
        return reverse('generate-thumbnail',
                       args=[size_fit, pathuri, thumburi])

    # If we're dealing with an image in media/public/..
    if parts[0] == 'public':
        # We actually want it to end up in media/public/thumbnails/..
        # since those files can be accessed without passing through a view.
        return settings.MEDIA_URL + thumbpath

    # Otherwise simply place it in media/thumbnails.
    # We provide a URL instead of calling it as a function, so that using
    # it means kicking off a new GET request. If we would generate all
    # thumbnails inline, loading an album overview would have high latency.
    if api:
        return reverse('private-thumbnails-api', args=[size_fit, path])
    return reverse('private-thumbnails', args=[size_fit, path])
