from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PushNotificationsConfig(AppConfig):
    name = 'pushnotifications'
    verbose_name = _('Push Notifications')
