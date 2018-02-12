from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EducationConfig(AppConfig):
    name = 'education'
    verbose_name = _('Education')
