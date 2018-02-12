from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MerchandiseConfig(AppConfig):
    name = 'merchandise'
    verbose_name = _('Merchandise')
