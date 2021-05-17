"""Configuration for the events package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EventsConfig(AppConfig):
    """AppConfig for the events package."""

    name = "events"
    verbose_name = _("Events")

    def ready(self):
        # pylint: disable=import-outside-toplevel
        from .payables import register

        register()
