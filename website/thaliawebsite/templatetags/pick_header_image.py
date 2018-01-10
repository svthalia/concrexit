import functools
import os
import random

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders


register = template.Library()
bannerdir = 'images/header_banners'


@functools.lru_cache()
def _banners():
    imgdir = finders.find(bannerdir)
    return [pic for pic in os.listdir(imgdir) if pic.endswith('.jpg')]


@register.simple_tag
def pick_header_image():
    """Renders a random header image"""
    return settings.STATIC_URL + bannerdir + '/' + random.choice(_banners())
