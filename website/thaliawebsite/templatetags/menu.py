"""Provides a template handler that renders the menu"""
from django import template
from django.urls import reverse

from ..menus import MAIN_MENU

register = template.Library()


@register.inclusion_tag("menu/menu.html", takes_context=True)
def render_main_menu(context):
    """
    Renders the main menu in this place.

    Accounts for logged-in status and locale.
    """

    path = None
    if "request" in context:
        path = context.get("request").path

    for item in MAIN_MENU:
        active = "name" in item and reverse(item["name"]) == path
        if not active and "submenu" in item:
            for subitem in item["submenu"]:
                if "name" in subitem and reverse(subitem["name"]) == path:
                    subitem["active"] = True
                    active = True
                else:
                    subitem["active"] = False
        item["active"] = active

    return {"menu": MAIN_MENU, "request": context.get("request")}
