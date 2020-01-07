from django import template

from utils.snippets import create_google_maps_url

register = template.Library()


@register.simple_tag()
def google_map_url(location, zoom=13, size="450x250"):
    return create_google_maps_url(location, zoom, size)
