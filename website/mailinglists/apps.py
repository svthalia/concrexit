from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MailinglistsConfig(AppConfig):
    name = 'mailinglists'
    verbose_name = _('Mailing lists')
