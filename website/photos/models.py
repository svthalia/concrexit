import hashlib
import logging
import os
import random

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from members.models import Member
from pushnotifications.models import ScheduledMessage, Category
from utils.translation import ModelTranslateMeta, MultilingualField

COVER_FILENAME = "cover.jpg"


logger = logging.getLogger(__name__)


def photo_uploadto(instance, filename):
    num = instance.album.photo_set.count()
    extension = os.path.splitext(filename)[1]
    new_filename = str(num).zfill(4) + extension
    return os.path.join(Album.photosdir, instance.album.dirname, new_filename)


class Photo(models.Model):

    album = models.ForeignKey(
        "Album", on_delete=models.CASCADE, verbose_name=_("album")
    )

    file = models.ImageField(_("file"), upload_to=photo_uploadto)

    rotation = models.IntegerField(
        verbose_name=_("rotation"),
        default=0,
        choices=((x, x) for x in (0, 90, 180, 270)),
        help_text=_("This does not modify the original image file."),
    )

    hidden = models.BooleanField(_("hidden"), default=False)

    _digest = models.CharField("digest", max_length=40,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.file:
            self.original_file = self.file.path
        else:
            self.original_file = ""

    def __str__(self):
        return os.path.basename(self.file.name)

    class Meta:
        ordering = ("file",)


class Album(models.Model, metaclass=ModelTranslateMeta):
    title = MultilingualField(models.CharField, _("title"), max_length=200,)

    dirname = models.CharField(verbose_name=_("directory name"), max_length=200,)

    date = models.DateField(verbose_name=_("date"),)

    slug = models.SlugField(verbose_name=_("slug"), unique=True,)

    hidden = models.BooleanField(verbose_name=_("hidden"), default=False)

    new_album_notification = models.ForeignKey(
        ScheduledMessage, on_delete=models.deletion.SET_NULL, blank=True, null=True
    )

    _cover = models.OneToOneField(
        Photo,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="covered_album",
        verbose_name=_("cover image"),
    )

    shareable = models.BooleanField(verbose_name=_("shareable"), default=False)

    photosdir = "photos"
    photospath = os.path.join(settings.MEDIA_ROOT, photosdir)

    @cached_property
    def cover(self):
        cover = None
        if self._cover is not None:
            return self._cover
        elif self.photo_set.exists():
            random.seed(self.dirname)
            cover = random.choice(self.photo_set.all())
        return cover

    def __str__(self):
        return "{} {}".format(self.date.strftime("%Y-%m-%d"), self.title)

    def get_absolute_url(self):
        return reverse("photos:album", args=[str(self.slug)])

    def save(self, *args, **kwargs):
        # dirname is only set for new objects, to avoid ever changing it
        if self.pk is None:
            self.dirname = self.slug

        if not self.hidden and (
            self.new_album_notification is None or not self.new_album_notification.sent
        ):
            new_album_notification_time = timezone.now() + timezone.timedelta(hours=1)
            new_album_notification = ScheduledMessage()

            if (
                self.new_album_notification is not None
                and not self.new_album_notification.sent
            ):
                new_album_notification = self.new_album_notification

            new_album_notification.title_en = "New album uploaded"
            new_album_notification.title_nl = "Nieuw album geüpload"
            new_album_notification.body_en = "A new photo album '{}' has just been uploaded".format(
                self.title_en
            )
            new_album_notification.body_nl = "Een nieuw fotoalbum '{}' is zojuist geüpload".format(
                self.title_nl
            )
            new_album_notification.category = Category.objects.get(key=Category.PHOTO)
            new_album_notification.url = (
                f"{settings.BASE_URL}" f"{self.get_absolute_url()}"
            )
            new_album_notification.time = new_album_notification_time
            new_album_notification.save()
            self.new_album_notification = new_album_notification
            self.new_album_notification.users.set(Member.current_members.all())
        elif (
            self.hidden
            and self.new_album_notification is not None
            and not self.new_album_notification.sent
        ):
            existing_notification = self.new_album_notification
            self.new_album_notification = None
            existing_notification.delete()

        super().save(*args, **kwargs)

    @property
    def access_token(self):
        return hashlib.sha256(
            "{}album{}".format(settings.SECRET_KEY, self.pk).encode("utf-8")
        ).hexdigest()

    class Meta:
        ordering = ("-date", "title_en")
