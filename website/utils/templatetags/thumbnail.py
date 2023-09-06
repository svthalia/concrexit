"""Thumbnail template tags."""

from django import template

from utils.media.services import get_thumbnail_url

register = template.Library()


@register.simple_tag
def thumbnail(path, size, absolute_url=False):
    """Generate a thumbnail for a path.

    This templatetag provides us with a way of getting a thumbnail
    directly inside templates. See the documentation
    of :func:`get_thumbnail_url` for a more information.
    :param path: The path or ImageField we want an thumbnail from,
    this field MUST NEVER be a user input.
    :param size: The size we want from settings.THUMBNAIL_SIZES.
    :param absolute_url: True if we want the full url including the scheme and domain.
    :return: The thumbnail url.
    """
    return get_thumbnail_url(path, size, absolute_url)
