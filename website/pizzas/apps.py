"""Configuration for the pizzas package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PizzasConfig(AppConfig):
    """AppConfig for the pizzas package."""

    name = "pizzas"
    verbose_name = _("Pizzas")

    def ready(self):
        """Import the signals when the app is ready."""
        # pylint: disable=unused-import,import-outside-toplevel
        from . import signals

        from .payables import register

        register()
