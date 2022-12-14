"""Configuration for the activemembers package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ActiveMembersConfig(AppConfig):
    """AppConfig for the activemembers package."""

    name = "activemembers"
    verbose_name = _("Active members")

    def ready(self):
        """Import the signals when the app is ready."""
        # pylint: disable=unused-import,import-outside-toplevel
        from . import signals

    def menu_items(self):
        return {
            "categories": [{"name": "association", "title": "Association", "key": 1}],
            "items": [
                {
                    "category": "association",
                    "title": "Board",
                    "viewname": "activemembers:boards",
                    "key": 0,
                },
                {
                    "category": "association",
                    "title": "Committees",
                    "viewname": "activemembers:committees",
                    "key": 1,
                },
                {
                    "category": "association",
                    "title": "Societies",
                    "viewname": "activemembers:societies",
                    "key": 2,
                },
            ],
        }
