from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

import os
import shutil

register = template.Library()


@register.simple_tag
def thumbnail(path, size, fit=False):
    parts = path.split('/')
    # If we're dealing with an image in media/public/..
    if parts[0] == 'public':
        # We actually want it to end up in media/public/thumbnails/..
        # since those files can be accessed without passing through a view.
        thumbpath = os.path.join(parts[0], 'thumbnails', *parts[1:])
    else:
        # Otherwise simply place it in media/thumbnails.
        thumbpath = os.path.join('thumbnails', path)

    full_thumbpath = os.path.join(settings.MEDIA_ROOT, thumbpath)
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    os.makedirs(os.path.dirname(full_thumbpath), exist_ok=True)

    # TODO actually create a thumbnail instead of copying
    shutil.copyfile(full_path, full_thumbpath)

    if parts[0] == 'public':
        return '/'.join([settings.MEDIA_URL, thumbpath])
    else:
        return reverse('private-thumbnails', args=[path])
