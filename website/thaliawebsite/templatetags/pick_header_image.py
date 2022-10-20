"""Get a random header image."""
import functools
import os
import random

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders

register = template.Library()
BANNERDIR = "img/headers"


@functools.lru_cache()
def _banners():
    """Get the available banners."""
    imgdir = finders.find(BANNERDIR)
    return [pic for pic in os.listdir(imgdir) if pic.endswith(".jpg")]


@register.simple_tag
def pick_header_image():
    """Render a random header image."""
    return settings.STATIC_URL + BANNERDIR + "/" + random.choice(_banners())
