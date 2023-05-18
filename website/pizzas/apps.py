"""Configuration for the pizzas package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PizzasConfig(AppConfig):
    """AppConfig for the pizzas package."""

    name = "pizzas"
    verbose_name = _("Pizzas")

    def ready(self):
        from .payables import register

        register()
