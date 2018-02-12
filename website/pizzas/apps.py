from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PizzasConfig(AppConfig):
    name = 'pizzas'
    verbose_name = _('Pizzas')
