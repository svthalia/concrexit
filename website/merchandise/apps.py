"""Contains the appconfig for the merchandise module."""

from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class MerchandiseConfig(AppConfig):
    """Configuration for the merchandise module."""

    name = "merchandise"
    verbose_name = _("Merchandise")

    def menu_items(self):
        return {
            "categories": [{"name": "association", "title": "Association", "key": 1}],
            "items": [
                {
                    "category": "association",
                    "title": "Merchandise",
                    "url": reverse("merchandise:index"),
                    "key": 4,
                },
            ],
        }

    def ready(self):
        """Register the payable when the app is ready."""
        from .payables import register

        register()
