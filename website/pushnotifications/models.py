import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from firebase_admin import exceptions, messaging


class Category(models.Model):
    """Describes a Message category."""

    # These should be the keys of the categories that we automatically created
    # in the migrations (0012 to be specific)
    GENERAL = "general"
    PIZZA = "pizza"
    EVENT = "event"
    NEWSLETTER = "newsletter"
    PARTNER = "partner"
    PHOTO = "photo"
    BOARD = "board"
    THABLOID = "thabloid"

    key = models.CharField(max_length=16, primary_key=True)

    name = models.CharField(
        _("name"),
        max_length=32,
    )

    description = models.TextField(_("description"), default="")

    def __str__(self):
        return self.name


def default_receive_category():
    return Category.objects.filter(key=Category.GENERAL)


class Device(models.Model):
    """Describes a device."""

    DEVICE_TYPES = (("ios", "iOS"), ("android", "Android"))

    registration_id = models.TextField(
        verbose_name=_("registration token"), unique=True
    )
    type = models.CharField(choices=DEVICE_TYPES, max_length=10)
    active = models.BooleanField(
        verbose_name=_("active"),
        default=True,
        help_text=_("Inactive devices will not be sent notifications"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False, null=False
    )
    date_created = models.DateTimeField(
        verbose_name=_("registration date"), auto_now_add=True, null=False
    )

    receive_category = models.ManyToManyField(
        Category, default=default_receive_category
    )

    class Meta:
        unique_together = (
            "registration_id",
            "user",
        )

    def __str__(self):
        return _("{user}s {device_type} device").format(
            user=self.user, device_type=self.type
        )


class NormalMessageManager(models.Manager):
    """Returns manual messages only."""

    def get_queryset(self):
        return super().get_queryset().filter(scheduledmessage__scheduled=None)


class MessageManager(models.Manager):
    """Returns all messages."""


class Message(models.Model):
    """Describes a push notification."""

    objects = NormalMessageManager()
    all_objects = MessageManager()

    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=150, verbose_name=_("title"))
    body = models.TextField(verbose_name=_("body"))
    url = models.CharField(
        verbose_name=_("url"),
        max_length=256,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_("category"),
        default="general",
    )
    sent = models.DateTimeField(
        verbose_name=_("sent"),
        null=True,
    )
    failure = models.IntegerField(
        verbose_name=_("failure"),
        blank=True,
        null=True,
    )
    success = models.IntegerField(
        verbose_name=_("success"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.title}: {self.body}"

    def send(self, **kwargs):
        if self:
            success_total = 0
            failure_total = 0
            ttl = kwargs.get("ttl", 3600)

            reg_ids = list(
                Device.objects.filter(
                    user__in=self.users.all(),
                    receive_category__key=self.category_id,
                    active=True,
                ).values_list("registration_id", flat=True)
            )

            data = kwargs.get("data", {})
            if self.url is not None:
                data["url"] = self.url
            data["title"] = self.title
            data["body"] = str(self.body)

            message = messaging.Message(
                notification=messaging.Notification(
                    title=data["title"],
                    body=data["body"],
                ),
                data=data,
                android=messaging.AndroidConfig(
                    ttl=datetime.timedelta(seconds=ttl),
                    priority="normal",
                    notification=messaging.AndroidNotification(
                        color="#E62272",
                        sound="default",
                    ),
                ),
            )

            for reg_id in reg_ids:
                message.token = reg_id
                try:
                    messaging.send(message, dry_run=kwargs.get("dry_run", False))
                    success_total += 1
                except messaging.UnregisteredError:
                    failure_total += 1
                    Device.objects.filter(registration_id=reg_id).delete()
                except exceptions.InvalidArgumentError:
                    failure_total += 1
                    Device.objects.filter(registration_id=reg_id).update(active=False)
                except exceptions.FirebaseError:
                    failure_total += 1

            self.sent = timezone.now()
            self.success = success_total
            self.failure = failure_total
            self.save()


class ScheduledMessageManager(models.Manager):
    """Returns scheduled messages only."""


class ScheduledMessage(Message):
    """Describes a scheduled push notification."""

    objects = ScheduledMessageManager()

    scheduled = models.BooleanField(default=True)
    time = models.DateTimeField()
    executed = models.DateTimeField(null=True)


class NewAlbumMessageManager(models.Manager):
    """Returns new album messages only."""


class NewAlbumMessage(ScheduledMessage):
    """A scheduled message to notify users of a new album."""

    objects = NewAlbumMessageManager()

    album = models.OneToOneField(
        "photos.Album",
        related_name="new_album_notification",
        on_delete=models.deletion.CASCADE,
    )


class FoodOrderReminderMessageManager(models.Manager):
    """Returns food event order end messages only."""


class FoodOrderReminderMessage(ScheduledMessage):
    """A scheduled message to notify users of a food order reminder."""

    objects = FoodOrderReminderMessageManager()

    food_event = models.OneToOneField(
        "pizzas.FoodEvent",
        related_name="end_reminder",
        on_delete=models.deletion.CASCADE,
    )


class RegistrationReminderMessageManager(models.Manager):
    """Returns event registration reminders only."""


class RegistrationReminderMessage(ScheduledMessage):
    """A scheduled message to notify users of something related to an event."""

    objects = RegistrationReminderMessageManager()

    event = models.OneToOneField(
        "events.Event",
        related_name="registration_reminder",
        on_delete=models.deletion.CASCADE,
    )


class EventStartReminderMessageManager(models.Manager):
    """Returns event start reminders only."""


class EventStartReminderMessage(ScheduledMessage):
    """A scheduled message to notify users of an event start."""

    objects = EventStartReminderMessageManager()

    event = models.OneToOneField(
        "events.Event",
        related_name="start_reminder",
        on_delete=models.deletion.CASCADE,
    )
