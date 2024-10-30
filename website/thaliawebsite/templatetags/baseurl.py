from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag()
def baseurl():
    """Return the BASE_URL defined in the settings."""
    return settings.BASE_URL
