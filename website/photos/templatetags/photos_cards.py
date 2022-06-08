from django import template
from django.conf import settings
from django.template.defaultfilters import date
from django.urls import reverse

from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_thumbnail_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def album_card(album):
    """Create a card to show on a page of multiple albums."""
    class_name = "album-card"
    image_url = ""

    if album.cover:
        image_url = get_thumbnail_url(
            album.cover.file, settings.THUMBNAIL_SIZES["medium"]
        )
        if album.cover.rotation > 0:
            class_name += " rotate{}".format(album.cover.rotation)

    url = album.get_absolute_url
    if not album.accessible:
        class_name += " grayscale"
        url = None

    return grid_item(
        title=album.title,
        meta_text="<p>{}</p>".format(date(album.date, "Y-m-d")),
        url=url,
        image_url=image_url,
        class_name=class_name,
    )


@register.inclusion_tag("includes/grid_item.html")
def photo_card(photo):
    """Create a card of a photo to show on an album page."""
    class_name = "photo-card"
    anchor_attrs = f'data-rotation="{photo.rotation}" data-fancybox="gallery"'

    if photo.album.shareable:
        anchor_attrs += " data-download-src={}".format(
            reverse(
                "photos:shared-download",
                args=[photo.album.slug, photo.album.access_token, photo],
            )
        )
    else:
        anchor_attrs += " data-download-src={}".format(
            reverse("photos:download", args=[photo.album.slug, photo])
        )

    anchor_attrs += " data-numLikes='{}'".format(photo.num_likes)

    anchor_attrs += " data-likeUrl={}".format(
        reverse("api:v2:photos:photo-like", args=[photo.pk])
    )

    image_url = get_thumbnail_url(photo.file, settings.THUMBNAIL_SIZES["medium"])

    if photo.rotation > 0:
        class_name += " rotate{}".format(photo.rotation)
        anchor_attrs += (
            f" data-options=" f'\'{{"slideClass": "rotate{photo.rotation}"}}\''
        )

    return grid_item(
        title="",
        meta_text=f"<p>{photo.num_likes} likes</p>",
        url=get_thumbnail_url(photo.file, settings.THUMBNAIL_SIZES["large"], fit=False),
        image_url=image_url,
        class_name=class_name,
        anchor_attrs=anchor_attrs,
    )
