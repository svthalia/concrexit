from django import template
from django.conf import settings
from django.templatetags import static

register = template.Library()


class FullStaticNode(static.StaticNode):
    """Static tag that always gives an absolute url.

    This gives an absolute url that can be used in emails,
    even when normal static urls are relative (`/static/...`).
    """

    def url(self, context):
        url = super().url(context)

        # If the url is not absolute, add the base url.
        if not url.startswith(("http://", "https://")):
            url = f"{settings.BASE_URL}{url}"

        return url


@register.tag("fullstatic")
def do_static(parser, token):
    return FullStaticNode.handle_token(parser, token)
