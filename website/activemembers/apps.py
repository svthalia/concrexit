from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ActiveMembersConfig(AppConfig):
    name = 'activemembers'
    verbose_name = _('Active members')
