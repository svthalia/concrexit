"""Configuration for the education package"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EducationConfig(AppConfig):
    """AppConfig for the education package"""
    name = 'education'
    verbose_name = _('Education')
