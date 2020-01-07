"""Configuration for the members package"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MembersConfig(AppConfig):
    name = "members"
    verbose_name = _("Members")
