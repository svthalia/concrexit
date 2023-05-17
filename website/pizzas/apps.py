"""Configuration for the pizzas package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from pizzas.services import execute_data_minimisation


class PizzasConfig(AppConfig):
    """AppConfig for the pizzas package."""

    name = "pizzas"
    verbose_name = _("Pizzas")

    def ready(self):
        # pylint: disable=unused-import,import-outside-toplevel
        from .payables import register

        register()

    def data_minimization_methods(self):
        return {"pizzas": execute_data_minimisation}
