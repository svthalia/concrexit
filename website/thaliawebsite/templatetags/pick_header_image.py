"""Get a random header image."""
import random

from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()

HEADERS = [
    "img/headers/banner_default.jpg",
    "img/headers/banner2.jpg",
    "img/headers/banner5.jpg",
    "img/headers/banner6.jpg",
    "img/headers/banner_new_Huygens.png",
    "img/headers/banner_new_Huygenstent.png",
    "img/headers/banner_new_robot.png",
    "img/headers/banner_new_tent.png",
]

HEADERS_FUN = [
    "img/headers/banner_new_wine.png",
    "img/headers/banner_new_winetasting.png",
    "img/headers/banner_new_christmas.png",
    "img/headers/banner_new_Huygenstent.png",
    "img/headers/banner_new_bingo.png",
    "img/headers/banner_new_food.png",
]


@register.simple_tag
def pick_header_image(type="normal"):
    """Render a random header image."""
    if type == "fun":
        headers = HEADERS_FUN
    else:
        headers = HEADERS
    return staticfiles_storage.url(random.choice(headers))
