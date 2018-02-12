from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnnouncementsConfig(AppConfig):
    name = 'announcements'
    verbose_name = _('Site header announcements')
