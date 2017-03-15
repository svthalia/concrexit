from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
import os
import random

register = template.Library()
banner_dir = static("/images/header_banners/")
current_dir = [pic for pic in os.listdir("thaliawebsite/" + banner_dir) if pic.endswith(".jpg")]


@register.simple_tag
def pick_header_image():
    return banner_dir + random.choice(current_dir)
