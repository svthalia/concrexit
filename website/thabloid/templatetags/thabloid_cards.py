from django import template
from django.urls import reverse

from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_thumbnail_url, get_media_url

register = template.Library()


@register.inclusion_tag("includes/grid_item.html", takes_context=True)
def thabloid_card(context, year, thabloid):
    request = context["request"]
    view_url = reverse("thabloid:pages", args=[thabloid.year, thabloid.issue])

    if request.member and request.member.current_membership is not None:
        buttons = (
            '<div class="text-center mt-2">'
            '<a href="{}" class="btn btn-secondary d-inline-flex open mr-1">'
            '<i class="fas fa-book-open"></i>'
            "</a>"
            '<a href="{}" download '
            'class="btn btn-secondary d-inline-flex download ml-1">'
            '<i class="fas fa-download"></i>'
            "</a>"
            "</div>"
        ).format(view_url, get_media_url(thabloid.file.path, attachment=True))
    else:
        buttons = (
            '<div class="text-center mt-2">'
            '<a href="{}" class="btn btn-secondary d-inline-flex open mr-1">'
            '<i class="fas fa-book-open"></i>'
            "</a>"
            "</div>"
        ).format(view_url)

    return grid_item(
        title="{}-{}, #{}".format(thabloid.year, thabloid.year + 1, thabloid.issue),
        meta_text=buttons,
        url=None,
        image_url=get_thumbnail_url(thabloid.cover, "255x360"),
        class_name=f"thabloid-card",
    )
