from django import template
from django.core.urlresolvers import resolve, reverse

from utils.templatetags.thumbnail import thumbnail

register = template.Library()


@register.simple_tag
def shared_thumbnail(slug, token, path, size, fit=True):
    thumb = resolve(thumbnail(path, size, fit))
    args = [slug, token, thumb.kwargs['size_fit'], thumb.kwargs['path']]
    return reverse('photos:shared-thumbnail', args=args)
