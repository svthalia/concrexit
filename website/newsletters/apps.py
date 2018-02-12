from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NewslettersConfig(AppConfig):
    name = 'newsletters'
    verbose_name = _('News letters')
