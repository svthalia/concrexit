"""Configuration for the payments package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    """AppConfig for the payments package."""

    name = "payments"
    verbose_name = _("Payments")

    def ready(self):
        """Import the signals when the app is ready."""
        # pylint: disable=unused-import,import-outside-toplevel
        from . import signals
