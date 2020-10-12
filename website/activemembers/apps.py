"""Configuration for the activemembers package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ActiveMembersConfig(AppConfig):
    """AppConfig for the activemembers package."""

    name = "activemembers"
    verbose_name = _("Active members")

    def ready(self):
        """Import the signals when the app is ready."""
        from . import signals
