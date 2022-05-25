"""Bleach allows to clean up user input to make it safe to display, but allow some HTML."""
from bleach import clean
from bleach.css_sanitizer import CSSSanitizer
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


def _allow_iframe_attrs(tag, name, value):
    """Filter to allow certain attributes for tags.

    :param tag: the tag
    :param name: the attribute name
    :param value: the value of the item.
    """
    # these are fine
    if name in ("class", "width", "height", "frameborder", "allowfullscreen"):
        return True

    # youtube is allowed to have `src`
    if tag == "iframe" and name == "src":
        return value.startswith("https://www.youtube.com/embed/") or value.startswith(
            "https://www.youtube-nocookie.com/embed/"
        )

    return False


@register.filter(is_safe=True)
@stringfilter
def bleach(value):
    """Bleach dangerous html from the input.

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
        '<img src="https://i.redd.it/22kypw2l93gz.jpg" alt="bees">'
        >>> bleach('<iframe width="560" height="315" '
        ... 'src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0" '
        ... 'frameborder="0" allowfullscreen></iframe>')
        <iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0" frameborder="0" allowfullscreen=""></iframe>
        >>> bleach('<iframe src="https://clearlyreta.rded.nl/ivo/"></iframe>')
        '<iframe></iframe>'
    """
    css_sanitizer = CSSSanitizer(allowed_css_properties=["text-decoration"])
    return mark_safe(
        clean(
            value,
            tags=[
                "h2",
                "h3",
                "p",
                "a",
                "div",
                "strong",
                "em",
                "i",
                "b",
                "ul",
                "li",
                "br",
                "ol",
                "iframe",
                "img",
                "span",
            ],
            attributes={
                "*": ["class", "style"],
                "iframe": _allow_iframe_attrs,
                "a": ["href", "rel", "target", "title"],
                "img": ["alt", "title", "src"],
            },
            css_sanitizer=css_sanitizer,
            strip=True,
        )
    )
