"""The models defined by the pushnotifications package"""
import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import override
from django.utils.translation import ugettext_lazy as _
from firebase_admin import messaging

from utils.translation import MultilingualField, ModelTranslateMeta


class Category(models.Model, metaclass=ModelTranslateMeta):
    """Describes a Message category"""

    key = models.CharField(max_length=16, primary_key=True)

    name = MultilingualField(
        models.CharField,
        _("name"),
        max_length=32,
    )

    description = MultilingualField(
        models.TextField,
        _("description"),
        default=""
    )

    def __str__(self):
        return self.name_en


def default_receive_category():
    return Category.objects.filter(key="general")


class Device(models.Model):
    """Describes a device"""

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
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


class MessageManager(models.Manager):
    """Returns manual messages only"""

    def get_queryset(self):
        return (super().get_queryset()
                .filter(scheduledmessage__task_id=None))


class Message(models.Model, metaclass=ModelTranslateMeta):
    """Describes a push notification"""

    objects = MessageManager()

    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    title = MultilingualField(
        models.CharField,
        max_length=150,
        verbose_name=_('title')
    )
    body = MultilingualField(
        models.TextField,
        verbose_name=_('body')
    )
    url = models.CharField(
        verbose_name=_('url'),
        max_length=256,
        null=True,
        blank=True,
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
            success_total = 0
            failure_total = 0
            ttl = kwargs.get('ttl', 3600)

            for lang in settings.LANGUAGES:
                with override(lang[0]):
                    reg_ids = list(
                        Device.objects.filter(
                            user__in=self.users.all(),
                            receive_category__key=self.category_id,
                            active=True,
                            language=lang[0]
                        ).values_list('registration_id', flat=True))

                    data = kwargs.get('data', {})
                    if self.url is not None:
                        data['url'] = self.url

                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=self.title,
                            body=str(self.body),
                        ),
                        data=data,
                        android=messaging.AndroidConfig(
                            ttl=datetime.timedelta(seconds=ttl),
                            priority='normal',
                            notification=messaging.AndroidNotification(
                                color='#E62272',
                                sound='default',
                            ),
                        ),
                    )

                    for reg_id in reg_ids:
                        message.token = reg_id
                        try:
                            messaging.send(message,dry_run=kwargs.get(
                                'dry_run', False))
                            success_total += 1
                        except messaging.ApiCallError as e:
                            failure_total += 1
                            d = Device.objects.filter(registration_id=reg_id)
                            if e.code == 'registration-token-not-registered':
                                d.delete()
                            elif (e.code == 'invalid-argument'
                                    or e.code == 'invalid-recipient'
                                    or e.code == 'invalid-registration-token'):
                                d.update(active=False)

            self.sent = True
            self.success = success_total
            self.failure = failure_total
            self.save()
        return None


class ScheduledMessageManager(models.Manager):
    """Returns scheduled messages only"""

    def get_queryset(self):
        return super().get_queryset()


class ScheduledMessage(Message, metaclass=ModelTranslateMeta):
    """Describes a scheduled push notification"""

    objects = ScheduledMessageManager()

    time = models.DateTimeField()
    executed = models.DateTimeField(null=True)
