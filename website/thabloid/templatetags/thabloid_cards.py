from django import template

from thabloid.models import Thabloid
from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_media_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def thabloid_card(thabloid: Thabloid):
    """Create a card for a thabloid to show on an overview of thabloids."""
    download_url = get_media_url(
        thabloid.file, attachment=f"thabloid-{thabloid.file.name}"
    )

    buttons = f"""
        <div class="text-center mt-2">
            <a href="{download_url}" download
               class="btn btn-secondary d-inline-flex download ms-1">
                <i class="fas fa-download"></i>
            </a>
        </div>
    """

    return grid_item(
        title=f"{thabloid.year}-{thabloid.year+1}, #{thabloid.issue}",
        meta_text=buttons,
        url=None,
        image_url=get_media_url(thabloid.cover),
        class_name="thabloid-card",
    )
