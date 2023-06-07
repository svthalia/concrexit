"""Configuration for the pushnotifications package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PushNotificationsConfig(AppConfig):
    """AppConfig for the pushnotifications package."""

    name = "pushnotifications"
    verbose_name = _("Push Notifications")

    def ready(self):
        """Import the signals when the app is ready."""
        from . import signals  # noqa: F401
