from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ThabloidConfig(AppConfig):
    """AppConfig for the Thabloid app."""

    name = "thabloid"
    verbose_name = _("Thabloid")
