"""Get a random header image."""
import random

from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.safestring import mark_safe

register = template.Library()

HEADERS = [
    "img/headers/banner_default",
    "img/headers/banner_bicycles",
    "img/headers/banner_huygenshall",
    "img/headers/banner_huygensfront",
    "img/headers/banner_huygens",
    "img/headers/banner_huygenstent",
    "img/headers/banner_robot",
    "img/headers/banner_tent",
]

HEADERS_FUN = [
    "img/headers/banner_wine",
    "img/headers/banner_winetasting",
    "img/headers/banner_christmas",
    "img/headers/banner_huygenstent",
    "img/headers/banner_bingo",
    "img/headers/banner_food",
]


@register.simple_tag
def pick_header_image(type="normal"):
    """Render a random header image."""
    if type == "fun":
        headers = HEADERS_FUN
    else:
        headers = HEADERS
    header = random.choice(headers)
    header_2k = staticfiles_storage.url(header + "-2k.webp")
    header_5k = staticfiles_storage.url(header + "-5k.webp")

    return mark_safe(f"{header_2k}, {header_5k} 3x")
