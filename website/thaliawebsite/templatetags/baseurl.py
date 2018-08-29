"""Obtain the base url"""
from django.template import Library

register = Library()  # pylint: disable=invalid-name


@register.simple_tag(takes_context=True)
def baseurl(context):
    """
    :return: a BASE_URL template context for the current request.
    """

    request = context['request']
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'

    return scheme + request.get_host()
