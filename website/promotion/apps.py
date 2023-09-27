"""Contains the appconfig for the promotion module."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PromotionConfig(AppConfig):
    """Configuration for the promotion module."""

    name = "promotion"
    verbose_name = _("Promotion")

    def ready(self):
        """Import the signals when the app is ready."""
        from . import signals  # noqa: F401
