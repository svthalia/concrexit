from django import template
from django.urls import reverse

from thabloid.models import Thabloid
from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_media_url, get_thumbnail_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def thabloid_card(thabloid: Thabloid):
    """Create a card for a thabloid to show on an overview of thabloids."""
    buttons = f"""
        <div class="text-center mt-2">
            <a href="{get_media_url(thabloid.file, attachment=True)}" download
               class="btn btn-secondary d-inline-flex download ms-1">
                <i class="fas fa-download"></i>
            </a>
        </div>
    """

    return grid_item(
        title=f"{thabloid.year}-{thabloid.year+1}, #{thabloid.issue}",
        meta_text=buttons,
        url=None,
        image_url=get_thumbnail_url(thabloid.cover, "255x360"),
        class_name="thabloid-card",
    )
