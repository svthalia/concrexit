from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ThabloidConfig(AppConfig):
    """AppConfig for the Thabloid app."""

    name = "thabloid"
    verbose_name = _("Thabloid")

    def menu_items(self):
        return {
            "categories": [{"name": "members", "title": "For Members", "key": 2}],
            "items": [
                {
                    "category": "members",
                    "title": "Thabloid",
                    "viewname": "thabloid:index",
                    "key": 5,
                }
            ],
        }
