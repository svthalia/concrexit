from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PartnersConfig(AppConfig):
    """Appconfig for partners app."""

    name = "partners"
    verbose_name = _("Partners")
