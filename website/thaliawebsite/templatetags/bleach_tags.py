from __future__ import unicode_literals, print_function, absolute_import

from bleach import clean
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def bleach(value):
    """Bleach dangerous html from the input"""

    return mark_safe(
        clean(
            value,
            tags=['h2', 'h3', 'p', 'a', 'div',
                  'strong', 'em', 'i', 'b', 'ul', 'li', 'br', 'ol'],
            attributes={
                '*': ['class'],
                'a': ['href', 'rel', 'target', 'title'],
                'img': ['alt', 'title'],
            },
            strip=True
        )
    )
