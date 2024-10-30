from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnnouncementsConfig(AppConfig):
    """AppConfig for the announcement package."""

    name = "announcements"
    verbose_name = _("Site announcements")
