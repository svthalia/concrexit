from __future__ import absolute_import, print_function, unicode_literals

from bleach import clean
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


def _allow_attributes(tag, name, value):
    if name in ('class', ):
        return True
    elif tag == 'a' and name in ('href', 'rel', 'target', 'title'):
        return True
    elif tag == 'img' and name in ('alt', 'title', 'src'):
        return True
    elif tag == 'iframe' and name in (
            'width', 'height', 'frameborder', 'allowfullscreen'):
        return True
    elif tag == 'iframe' and name == 'src':
        if (value.startswith('https://www.youtube.com/embed/') or
                value.startswith('https://www.youtube-nocookie.com/embed/')):
            return True
        else:
            return False

    return False


@register.filter(is_safe=True)
@stringfilter
def bleach(value):
    """Bleach dangerous html from the input

    Examples::

        >>> bleach('<script></script>')
        ''
        >>> bleach('simple')
        'simple'
        >>> bleach('<a href="http://example.com/">ex</a>')
        '<a href="http://example.com/">ex</a>'
        >>> bleach('<div class="bla"></div>')
        '<div class="bla"></div>'
        >>> bleach('<img src="https://i.redd.it/22kypw2l93gz.jpg" alt="bees">')
        '<img alt="bees" src="https://i.redd.it/22kypw2l93gz.jpg">'
        >>> bleach('<iframe width="560" height="315" '
        ... 'src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0" '
        ... 'frameborder="0" allowfullscreen></iframe>') == (
        ...     '<iframe allowfullscreen="" frameborder="0" height="315" '
        ...     'src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0" '
        ...     'width="560"></iframe>')
        True
        >>> bleach('<iframe src="https://clearlyreta.rded.nl/ivo/"></iframe>')
        '<iframe></iframe>'
    """

    return mark_safe(
        clean(
            value,
            tags=(
                'h2', 'h3', 'p', 'a', 'div',
                'strong', 'em', 'i', 'b', 'ul', 'li', 'br', 'ol',
                'iframe', 'img'
            ),
            attributes=_allow_attributes,
            strip=True
        )
    )
