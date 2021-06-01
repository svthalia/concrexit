"""Configuration for the payments package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    """AppConfig for the payments package."""

    name = "payments"
    verbose_name = _("Payments")
