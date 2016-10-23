import os

from django import template
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from django.urls import reverse
from PIL import Image, ImageOps

register = template.Library()


@register.simple_tag
def thumbnail(path, size, fit=True):
    if isinstance(path, ImageFieldFile):
        path = path.name

    size_fit = '{}_{}'.format(size, int(fit))

    parts = path.split('/')
    # If we're dealing with an image in media/public/..
    if parts[0] == 'public':
        # We actually want it to end up in media/public/thumbnails/..
        # since those files can be accessed without passing through a view.
        thumbpath = os.path.join(parts[0], 'thumbnails', size_fit, *parts[1:])
    else:
        # Otherwise simply place it in media/thumbnails.
        thumbpath = os.path.join('thumbnails', size_fit, path)

    full_thumbpath = os.path.join(settings.MEDIA_ROOT, thumbpath)
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    os.makedirs(os.path.dirname(full_thumbpath), exist_ok=True)

    if (not os.path.isfile(full_thumbpath) or
            os.path.getmtime(full_path) > os.path.getmtime(full_thumbpath)):
        image = Image.open(full_path)
        size = tuple(int(dim) for dim in size.split('x'))
        if not fit:
            ratio = min([a / b for a, b in zip(size, image.size)])
            size = tuple(int(ratio * x) for x in image.size)
        thumb = ImageOps.fit(image, size, Image.ANTIALIAS)
        thumb.save(full_thumbpath)

    if parts[0] == 'public':
        return settings.MEDIA_URL + thumbpath
    else:
        return reverse('private-thumbnails', args=[size_fit, path])
