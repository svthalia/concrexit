"""Configuration for the newsletters package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RegistrationsConfig(AppConfig):
    """AppConfig for the registrations package."""

    name = "registrations"
    verbose_name = _("Registrations")

    def ready(self):
        """Import the signals when the app is ready."""
        # pylint: disable=unused-import,import-outside-toplevel
        from . import signals
        from .payables import register

        register()
