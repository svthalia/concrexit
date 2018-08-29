"""Provides a template handler that renders the menu"""
from django import template

from ..menus import MAIN_MENU

register = template.Library()  # pylint: disable=invalid-name


@register.inclusion_tag('menu/menu.html', takes_context=True)
def render_main_menu(context):
    """
    Renders the main menu in this place.

    Accounts for logged-in status and locale.
    """
    return {'menu': MAIN_MENU, 'request': context.get('request')}
