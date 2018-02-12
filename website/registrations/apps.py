from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class RegistrationsConfig(AppConfig):
    name = 'registrations'
    verbose_name = _('Registrations')

    def ready(self):
        from . import signals  # noqa: F401
