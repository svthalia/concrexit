"""Obtain the base url"""
from django.conf import settings
from django.template import Library

register = Library()  # pylint: disable=invalid-name


@register.simple_tag()
def baseurl():
    """
    :return: the BASE_URL defined in the settings
    """

    return settings.BASE_URL
