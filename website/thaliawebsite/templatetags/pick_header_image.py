from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
import os, random

register = template.Library()
banner_dir = static("/images/header_banners/")
current_dir = os.listdir("." + banner_dir)


@register.simple_tag
def pick_header_image():
    return banner_dir + random.choice(current_dir)
