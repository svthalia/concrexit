from __future__ import unicode_literals

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import override
from pyfcm import FCMNotification

from thaliawebsite import settings
from utils.translation import MultilingualField, ModelTranslateMeta


class Category(models.Model, metaclass=ModelTranslateMeta):
    key = models.CharField(max_length=16, primary_key=True)

    name = MultilingualField(
        models.CharField,
        _("name"),
        max_length=32,
    )

    def __str__(self):
        return self.name_en


def default_receive_category():
    return Category.objects.filter(key="general")


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
                             on_delete=models.CASCADE,
                             blank=False,
                             null=False)
    date_created = models.DateTimeField(
        verbose_name=_("registration date"), auto_now_add=True, null=False
    )
    language = models.CharField(
        verbose_name=_('language'),
        max_length=2,
        choices=settings.LANGUAGES,
        default='en',
    )

    receive_category = models.ManyToManyField(
        Category,
        default=default_receive_category
    )

    class Meta:
        unique_together = ('registration_id', 'user',)


class Message(models.Model, metaclass=ModelTranslateMeta):
    GENERAL = 'general'
    PIZZA = 'pizza'
    EVENT = 'event'
    NEWSLETTER = 'newsletter'
    SPONSOR = 'sponsor'
    PHOTO = 'photo'
    BOARD = 'board'

    CATEGORIES = (
        (GENERAL, _("General")),
        (PIZZA, _("Pizza")),
        (EVENT, _("Events")),
        (NEWSLETTER, _("Newsletter")),
        (SPONSOR, _("Sponsored messages")),
        (PHOTO, _("Photos")),
        (BOARD, _("Board")),
    )

    users = models.ManyToManyField(django_settings.AUTH_USER_MODEL)
    title = MultilingualField(
        models.CharField,
        max_length=150,
        verbose_name=_('title')
    )
    body = MultilingualField(
        models.TextField,
        verbose_name=_('body')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_('category'),
        default="general"
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
            any_reg_ids = False
            success_total = 0
            failure_total = 0
            result_list = []

            for lang in settings.LANGUAGES:
                with override(lang[0]):
                    reg_ids = list(
                        Device.objects.filter(
                            user__in=self.users.all(),
                            receive_category__key=self.category_id,
                            active=True,
                            language=lang[0]
                        ).values_list('registration_id', flat=True))

                    if len(reg_ids) == 0:
                        continue

                    any_reg_ids = True

                    result = FCMNotification(
                        api_key=settings.PUSH_NOTIFICATIONS_API_KEY
                    ).notify_multiple_devices(
                        registration_ids=reg_ids,
                        message_title=self.title,
                        message_body=str(self.body),
                        color='#E62272',
                        sound='default',
                        **kwargs
                    )

                    results = result['results']
                    for (index, item) in enumerate(results):
                        if 'error' in item:
                            reg_id = reg_ids[index]

                            if (item['error'] == 'NotRegistered'
                                    or item['error'] == 'InvalidRegistration'):
                                Device.objects.filter(
                                    registration_id=reg_id).delete()
                            else:
                                Device.objects.filter(
                                    registration_id=reg_id
                                ).update(active=False)

                    success_total += result['success']
                    failure_total += result['failure']
                    result_list.append(result)

            if any_reg_ids:
                self.sent = True
                self.success = success_total
                self.failure = failure_total
                self.save()

            return result_list
        return None
