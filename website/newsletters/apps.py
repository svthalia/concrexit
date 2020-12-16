"""Configuration for the newsletters package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NewslettersConfig(AppConfig):
    """AppConfig for the newsletters package."""

    name = "newsletters"
    verbose_name = _("Newsletters")
