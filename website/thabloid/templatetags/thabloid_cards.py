from django import template
from django.urls import reverse

from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_thumbnail_url, get_media_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def thabloid_card(year, thabloid):
    """Create a card for a thabloid to show on an overview of thabloids."""
    view_url = reverse("thabloid:pages", args=[thabloid.year, thabloid.issue])
    buttons = (
        '<div class="text-center mt-2">'
        f'<a href="{view_url}" class="btn btn-secondary d-inline-flex open me-1">'
        '<i class="fas fa-book-open"></i>'
        "</a>"
        f'<a href="{get_media_url(thabloid.file, attachment=True)}" download '
        'class="btn btn-secondary d-inline-flex download ms-1">'
        '<i class="fas fa-download"></i>'
        "</a>"
        "</div>"
    )

    return grid_item(
        title=f"{thabloid.year}-{thabloid.year+1}, #{thabloid.issue}",
        meta_text=buttons,
        url=None,
        image_url=get_thumbnail_url(thabloid.cover, "255x360"),
        class_name="thabloid-card",
    )
