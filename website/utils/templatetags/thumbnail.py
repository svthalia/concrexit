"""Thumbnail template tags"""

from django import template

from utils.media.services import get_thumbnail_url

register = template.Library()  # pylint: disable=invalid-name


@register.simple_tag
def thumbnail(path, size, fit=True):
    """
    This templatetag provides us with a way of getting a thumbnail
    directly inside templates. See the documentation
    of :func:`get_thumbnail_url` for a more information.
    :param path: the path or ImageField we want an thumbnail from,
    this field MUST NEVER be a user input
    :param size: the size formatted like `widthxheight`
    :param fit: True if we want the image to fit
    :return: the thumbnail url
    """
    return get_thumbnail_url(path, size, fit)
