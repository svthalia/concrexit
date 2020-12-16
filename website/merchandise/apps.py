"""Contains the appconfig for the merchandise module."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MerchandiseConfig(AppConfig):
    """Configuration for the merchandise module."""

    name = "merchandise"
    verbose_name = _("Merchandise")
