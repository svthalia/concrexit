from django import template
from django.conf import settings
from django.template.defaultfilters import date
from django.urls import reverse
from photos.templatetags.shared_thumbnail import shared_thumbnail

from thaliawebsite.templatetags.grid_item import grid_item
from utils.templatetags.thumbnail import thumbnail

register = template.Library()


@register.inclusion_tag('includes/grid_item.html')
def album_card(album):
    class_name = 'album-card'
    image_url = ''

    if album.cover:
        image_url = thumbnail(album.cover.file,
                              settings.THUMBNAIL_SIZES['medium'])
        if album.cover.rotation > 0:
            class_name += ' rotate{}'.format(album.cover.rotation)

    if not album.accessible:
        class_name += ' grayscale'

    return grid_item(
        title=album.title,
        meta_text='<p>{}</p>'.format(date(album.date, 'Y-m-d')),
        url=album.get_absolute_url,
        image_url=image_url,
        class_name=class_name,
    )


@register.inclusion_tag('includes/grid_item.html')
def photo_card(photo):
    class_name = 'photo-card rotate{}'.format(photo.rotation)
    anchor_attrs = (f'data-fancybox-rotation="{photo.rotation}" '
                    f'data-fancybox="gallery"')

    if photo.album.shareable:
        anchor_attrs += ' data-download={}'.format(
            reverse('photos:shared-download',
                    args=[photo.album.slug, photo.album.access_token, photo]))
    else:
        anchor_attrs += ' data-download={}'.format(
            reverse('photos:download', args=[photo.album.slug, photo]))

    image_url = thumbnail(photo.file, settings.THUMBNAIL_SIZES['medium'])
    if photo.album.shareable:
        image_url = shared_thumbnail(photo.album.slug,
                                     photo.album.access_token, photo.file,
                                     settings.THUMBNAIL_SIZES['medium'])

    if photo.rotation > 0:
        class_name += ' rotate{}'.format(photo.rotation)

    return grid_item(
        title='',
        url=thumbnail(photo.file, settings.THUMBNAIL_SIZES['large'],
                      fit=False),
        image_url=image_url,
        class_name=class_name,
        anchor_attrs=anchor_attrs
    )
