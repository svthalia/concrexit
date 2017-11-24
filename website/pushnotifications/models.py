from __future__ import unicode_literals

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from pyfcm import FCMNotification

from thaliawebsite import settings


class Device(models.Model):
    DEVICE_TYPES = (
        ('ios', 'iOS'),
        ('android', 'Android')
    )

    registration_id = models.TextField(verbose_name=_("registration token"))
    type = models.CharField(choices=DEVICE_TYPES, max_length=10)
    active = models.BooleanField(
        verbose_name=_("active"), default=True,
        help_text=_("Inactive devices will not be sent notifications")
    )
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL,
                             blank=False, null=False)
    date_created = models.DateTimeField(
        verbose_name=_("registration date"), auto_now_add=True, null=False
    )
    language = models.CharField(
        verbose_name=_('language'),
        max_length=2,
        choices=settings.LANGUAGES,
    )

    class Meta:
        unique_together = ('registration_id', 'user',)


class Message(models.Model):

    users = models.ManyToManyField(django_settings.AUTH_USER_MODEL)
    title = models.CharField(
        max_length=150,
        verbose_name=_('title')
    )
    body = models.TextField(
        verbose_name=_('body')
    )

    sent = models.BooleanField(
        verbose_name=_('sent'),
        default=False
    )
    failure = models.IntegerField(
        verbose_name=_('failure'),
        blank=True,
        null=True,
    )
    success = models.IntegerField(
        verbose_name=_('success'),
        blank=True,
        null=True,
    )

    def __str__(self):
        return '{}: {}'.format(self.title, self.body)

    def send(self, **kwargs):
        if self:
            reg_ids = list(
                Device.objects.filter(user__in=self.users.all(), active=True)
                              .values_list('registration_id', flat=True))
            if len(reg_ids) == 0:
                return None

            result = FCMNotification(
                api_key=settings.PUSH_NOTIFICATIONS_API_KEY
            ).notify_multiple_devices(
                registration_ids=reg_ids,
                message_title=self.title,
                message_body=self.body,
                color='#E62272',
                sound='default',
                **kwargs
            )

            results = result['results']
            for (index, item) in enumerate(results):
                if 'error' in item:
                    reg_id = reg_ids[index]

                    if (item['error'] == 'NotRegistered' or
                            item['error'] == 'InvalidRegistration'):
                        Device.objects.filter(registration_id=reg_id).delete()
                    else:
                        Device.objects.filter(
                            registration_id=reg_id).update(active=False)

            self.sent = True
            self.success = result['success']
            self.failure = result['failure']
            self.save()

            return result
        return None
