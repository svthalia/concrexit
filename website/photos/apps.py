from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class PhotosConfig(AppConfig):
    """AppConfig class for Photos app."""

    name = "photos"
    verbose_name = _("Photos")

    def ready(self):
        """Import the signals when the app is ready."""
        super().ready()
        # pylint: disable=unused-import,import-outside-toplevel
        from . import signals

    def menu_items(self):
        return {
            "categories": [{"name": "members", "title": "For Members", "key": 2}],
            "items": [
                {
                    "category": "members",
                    "title": "Photos",
                    "url": reverse("photos:index"),
                    "key": 1,
                }
            ],
        }
