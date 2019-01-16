from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PizzasConfig(AppConfig):
    name = 'pizzas'
    verbose_name = _('Pizzas')

    def ready(self):
        """Imports the signals when the app is ready"""
        from . import signals  # noqa: F401
