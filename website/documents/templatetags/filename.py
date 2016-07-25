from django import template

import os


register = template.Library()


@register.filter
def filename(value):
    return os.path.basename(value.file.name)
