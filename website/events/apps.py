"""Configuration for the events package."""
from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class EventsConfig(AppConfig):
    """AppConfig for the events package."""

    name = "events"
    verbose_name = _("Events")

    def ready(self):
        from . import signals  # noqa: F401
        from .payables import register

        register()

    def menu_items(self):
        return {
            "categories": [{"name": "association", "title": "Association", "key": 1}],
            "items": [
                {
                    "category": "association",
                    "title": "Alumni",
                    "url": reverse("events:alumni"),
                    "key": 7,
                },
                {
                    "title": "Calendar",
                    "url": reverse("events:index"),
                    "key": 3,
                },
            ],
        }
