from django import template
from django.conf import settings
from django.template.defaultfilters import date
from django.urls import reverse

from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_media_url, get_thumbnail_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def album_card(album):
    """Create a card to show on a page of multiple albums."""
    class_name = "album-card"
    image_url = ""

    if album.cover:
        image_url = album.cover.file.thumbnails.medium.url
        if album.cover.rotation > 0:
            class_name += f" rotate{album.cover.rotation}"

    url = album.get_absolute_url
    if not album.accessible:
        class_name += " grayscale"
        url = None

    return grid_item(
        title=album.title,
        meta_text=f'<p>{date(album.date, "Y-m-d")}</p>',
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
        url = reverse(
            "photos:shared-download",
            args=[photo.album.slug, photo.album.access_token, photo],
        )
        anchor_attrs += f" data-download-src={url}"
    else:
        url = reverse("photos:download", args=[photo.album.slug, photo])
        anchor_attrs += f" data-download-src={url}"

    anchor_attrs += f" data-numLikes='{photo.num_likes}'"
    anchor_attrs += (
        f" data-likeUrl={reverse('api:v2:photos:photo-like', args=[photo.pk])}"
    )

    image_url = get_media_url(photo.file.thumbnails.medium)

    if photo.rotation > 0:
        class_name += f" rotate{photo.rotation}"
        anchor_attrs += (
            f" data-options=" f'\'{{"slideClass": "rotate{photo.rotation}"}}\''
        )

    return grid_item(
        title="",
        meta_text=f"<p><i class='fas fa-heart me-2'></i>{photo.num_likes}</p>",
        url=photo.file.url,
        image_url=image_url,
        class_name=class_name,
        anchor_attrs=anchor_attrs,
    )


@register.inclusion_tag("includes/grid_item.html")
def liked_photo_card(photo):
    card = photo_card(photo)
    card.update({"meta_text": ""})
    return card
