from django import template
from django.urls import resolve, reverse

from os.path import basename

from utils.templatetags.thumbnail import thumbnail

register = template.Library()


@register.simple_tag
def shared_thumbnail(slug, token, path, size, fit=True):
    thumb = resolve(thumbnail(path, size, fit))
    filename = basename(thumb.kwargs['path'])
    args = [slug, thumb.kwargs['size_fit'], token, filename]
    return reverse('photos:shared-thumbnail', args=args)
