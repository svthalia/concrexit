"""Get a random header image."""
import random

from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()

HEADERS = [
    "img/headers/banner_default.jpg",
    "img/headers/banner2.jpg",
    "img/headers/banner4.jpg",
    "img/headers/banner5.jpg",
    "img/headers/banner6.jpg",
]


@register.simple_tag
def pick_header_image():
    """Render a random header image."""
    return staticfiles_storage.url(random.choice(HEADERS))
