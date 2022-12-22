"""Provides a template handler that renders the menu."""
from collections import defaultdict
from functools import cache

from django import template
from django.apps import apps

register = template.Library()


@cache
def collect_menus():
    categories = defaultdict(lambda: [])
    main_menu = []

    for app in apps.get_app_configs():
        if hasattr(app, "menu_items"):
            menu = app.menu_items()
            if "categories" in menu:
                for category in menu["categories"]:
                    assert "key" in category
                    if category["name"] not in categories:
                        categories[category["name"]] = {"items": [], **category}

            for item in menu["items"]:
                assert "url" in item, item
                if "category" not in item:
                    # Main item
                    main_menu.append(item)
                else:
                    assert item["category"] in categories

                    categories[item["category"]]["items"].append(item)

    for category in categories.values():
        main_menu.append(
            {
                "submenu": sorted(
                    category["items"], key=lambda x: (x["key"], x["title"])
                ),
                **category,
            }
        )
    return sorted(main_menu, key=lambda x: (x["key"], x["title"]))


@register.inclusion_tag("menu/menu.html", takes_context=True)
def render_main_menu(context):
    """Render the main menu in this place.

    Accounts for logged-in status and locale.
    """
    path = None
    if "request" in context:
        path = context.get("request").path

    main_menu = collect_menus()

    for item in main_menu:
        active = "url" in item and item["url"] == path
        if not active and "submenu" in item:
            for subitem in item["submenu"]:
                if subitem["url"] == path:
                    subitem["active"] = True
                    active = True
                else:
                    subitem["active"] = False
        item["active"] = active

    return {"menu": main_menu, "request": context.get("request")}
