from django import template

from ..menus import main

register = template.Library()


@register.inclusion_tag('menu/menu.html', takes_context=True)
def render_main_menu(context):
    return {'menu': main, 'request': context.get('request')}
