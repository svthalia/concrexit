"""Configuration for the newsletters package"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class RegistrationsConfig(AppConfig):
    """AppConfig for the registrations package"""

    name = "registrations"
    verbose_name = _("Registrations")

    def ready(self):
        """Imports the signals when the app is ready"""
        from . import signals  # noqa: F401
