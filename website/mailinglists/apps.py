"""Configuration for the mailinglists package"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MailinglistsConfig(AppConfig):
    """Appconfig for mailinglist app."""

    name = 'mailinglists'
    verbose_name = _('Mailing lists')

    def ready(self):
        """Imports the signals when the app is ready"""
        from . import signals  # noqa: F401
