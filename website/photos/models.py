import hashlib
import logging
import os
import random

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Value, IntegerField
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from queryable_properties.properties import AnnotationProperty

from members.models import Member
from events.models import Event
from pushnotifications.models import ScheduledMessage, Category

COVER_FILENAME = "cover.jpg"


logger = logging.getLogger(__name__)


def photo_uploadto(instance, filename):
    """Get path of file to upload to."""
    num = instance.album.photo_set.count()
    extension = os.path.splitext(filename)[1]
    new_filename = str(num).zfill(4) + extension
    return os.path.join(Album.photosdir, instance.album.dirname, new_filename)


class Photo(models.Model):
    """Model for a Photo object."""

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

    _digest = models.CharField(
        "digest",
        max_length=40,
    )

    num_likes = AnnotationProperty(
        Coalesce(Count("likes"), Value(0), output__field=IntegerField())
    )

    face_recognition_processed = models.BooleanField(
        verbose_name=_("face encodings processed"), default=False
    )

    num_faces = AnnotationProperty(
        Coalesce(Count("face_encodings"), Value(0), output__field=IntegerField())
    )

    def __init__(self, *args, **kwargs):
        """Initialize Photo object and set the file if it exists."""
        super().__init__(*args, **kwargs)
        if self.file:
            self.original_file = self.file.name
        else:
            self.original_file = ""

    def __str__(self):
        """Return the filename of a Photo object."""
        return os.path.basename(self.file.name)

    def delete(self, using=None, keep_parents=False):
        removed = super().delete(using, keep_parents)
        if self.file.name:
            self.file.delete()
        return removed

    class Meta:
        """Meta class for Photo."""

        ordering = ("file",)


class Like(models.Model):
    photo = models.ForeignKey(
        Photo,
        verbose_name=_("Photo"),
        null=False,
        blank=False,
        related_name="likes",
        on_delete=models.CASCADE,
    )
    member = models.ForeignKey(
        Member,
        verbose_name=_("Member"),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return str(self.member) + " " + _("likes") + " " + str(self.photo)

    class Meta:
        unique_together = ["photo", "member"]


# class PersonOnPhoto(models.Model):
#     photo = models.ForeignKey(
#         Photo,
#         verbose_name=_("Photo"),
#         null=False,
#         blank=False,
#         related_name="persons",
#         on_delete=models.CASCADE,
#     )
#     member = models.ForeignKey(
#         Member,
#         verbose_name=_("Member"),
#         null=True,
#         blank=False,
#         on_delete=models.SET_NULL,
#     )
#     self_indicated = models.BooleanField(
#         verbose_name=_("Self-indicated"), default=False
#     )
#
#     def __str__(self):
#         return str(self.member) + " " + _("is on") + " " + str(self.photo)
#
#     class Meta:
#         unique_together = ["photo", "member"]


class FaceEncoding(models.Model):
    photo = models.ForeignKey(
        Photo,
        verbose_name=_("Photo"),
        null=True,
        related_name="face_encodings",
        on_delete=models.CASCADE,
    )

    _field0 = models.FloatField()
    _field1 = models.FloatField()
    _field2 = models.FloatField()
    _field3 = models.FloatField()
    _field4 = models.FloatField()
    _field5 = models.FloatField()
    _field6 = models.FloatField()
    _field7 = models.FloatField()
    _field8 = models.FloatField()
    _field9 = models.FloatField()
    _field10 = models.FloatField()
    _field11 = models.FloatField()
    _field12 = models.FloatField()
    _field13 = models.FloatField()
    _field14 = models.FloatField()
    _field15 = models.FloatField()
    _field16 = models.FloatField()
    _field17 = models.FloatField()
    _field18 = models.FloatField()
    _field19 = models.FloatField()
    _field20 = models.FloatField()
    _field21 = models.FloatField()
    _field22 = models.FloatField()
    _field23 = models.FloatField()
    _field24 = models.FloatField()
    _field25 = models.FloatField()
    _field26 = models.FloatField()
    _field27 = models.FloatField()
    _field28 = models.FloatField()
    _field29 = models.FloatField()
    _field30 = models.FloatField()
    _field31 = models.FloatField()
    _field32 = models.FloatField()
    _field33 = models.FloatField()
    _field34 = models.FloatField()
    _field35 = models.FloatField()
    _field36 = models.FloatField()
    _field37 = models.FloatField()
    _field38 = models.FloatField()
    _field39 = models.FloatField()
    _field40 = models.FloatField()
    _field41 = models.FloatField()
    _field42 = models.FloatField()
    _field43 = models.FloatField()
    _field44 = models.FloatField()
    _field45 = models.FloatField()
    _field46 = models.FloatField()
    _field47 = models.FloatField()
    _field48 = models.FloatField()
    _field49 = models.FloatField()
    _field50 = models.FloatField()
    _field51 = models.FloatField()
    _field52 = models.FloatField()
    _field53 = models.FloatField()
    _field54 = models.FloatField()
    _field55 = models.FloatField()
    _field56 = models.FloatField()
    _field57 = models.FloatField()
    _field58 = models.FloatField()
    _field59 = models.FloatField()
    _field60 = models.FloatField()
    _field61 = models.FloatField()
    _field62 = models.FloatField()
    _field63 = models.FloatField()
    _field64 = models.FloatField()
    _field65 = models.FloatField()
    _field66 = models.FloatField()
    _field67 = models.FloatField()
    _field68 = models.FloatField()
    _field69 = models.FloatField()
    _field70 = models.FloatField()
    _field71 = models.FloatField()
    _field72 = models.FloatField()
    _field73 = models.FloatField()
    _field74 = models.FloatField()
    _field75 = models.FloatField()
    _field76 = models.FloatField()
    _field77 = models.FloatField()
    _field78 = models.FloatField()
    _field79 = models.FloatField()
    _field80 = models.FloatField()
    _field81 = models.FloatField()
    _field82 = models.FloatField()
    _field83 = models.FloatField()
    _field84 = models.FloatField()
    _field85 = models.FloatField()
    _field86 = models.FloatField()
    _field87 = models.FloatField()
    _field88 = models.FloatField()
    _field89 = models.FloatField()
    _field90 = models.FloatField()
    _field91 = models.FloatField()
    _field92 = models.FloatField()
    _field93 = models.FloatField()
    _field94 = models.FloatField()
    _field95 = models.FloatField()
    _field96 = models.FloatField()
    _field97 = models.FloatField()
    _field98 = models.FloatField()
    _field99 = models.FloatField()
    _field100 = models.FloatField()
    _field101 = models.FloatField()
    _field102 = models.FloatField()
    _field103 = models.FloatField()
    _field104 = models.FloatField()
    _field105 = models.FloatField()
    _field106 = models.FloatField()
    _field107 = models.FloatField()
    _field108 = models.FloatField()
    _field109 = models.FloatField()
    _field110 = models.FloatField()
    _field111 = models.FloatField()
    _field112 = models.FloatField()
    _field113 = models.FloatField()
    _field114 = models.FloatField()
    _field115 = models.FloatField()
    _field116 = models.FloatField()
    _field117 = models.FloatField()
    _field118 = models.FloatField()
    _field119 = models.FloatField()
    _field120 = models.FloatField()
    _field121 = models.FloatField()
    _field122 = models.FloatField()
    _field123 = models.FloatField()
    _field124 = models.FloatField()
    _field125 = models.FloatField()
    _field126 = models.FloatField()
    _field127 = models.FloatField()

    @property
    def encoding(self):
        return [getattr(self, f"_field{i}") for i in range(0, 128)]

    @encoding.setter
    def encoding(self, value):
        for i in range(0, 128):
            setattr(self, f"_field{i}", value[i])

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert, force_update, using, update_fields)
        if self.photo:
            self.photo.face_encodings_processed = True
            self.photo.save()

        if self.encoding:
            self.match_faces()

    def __str__(self):
        return f"FaceEncoding {self.id}"

    def match_faces(self):
        matches = FaceEncoding.objects.filter(photo__isnull=True).extra(
            where=[face_recognition_distance_function(self.encoding)]
        )

        for reference_face in self.matches.all():
            if reference_face.encoding not in matches:
                self.matches.remove(reference_face)
        for encoding in matches.all():
            self.matches.add(encoding.reference_face)


def face_recognition_distance_function(encoding):
    distance_function = "sqrt("
    for i in range(0, 128):
        distance_function += f"power(_field{i} - {encoding[i]}, 2) + "
    distance_function = distance_function[0:-2] + "),"
    distance_function = distance_function[0:-1]
    return f"{distance_function} < 0.49"


def reference_face_uploadto(instance, filename):
    """Get path of file to upload to."""
    num = instance.member.reference_faces.all().count()
    extension = os.path.splitext(filename)[1]
    new_filename = str(num).zfill(4) + extension
    return os.path.join(
        "face_recognition/reference_faces", instance.member.username, new_filename
    )


class ReferenceFace(models.Model):
    member = models.ForeignKey(
        Member,
        verbose_name=_("Member"),
        on_delete=models.CASCADE,
        related_name="reference_faces",
    )
    encoding = models.OneToOneField(
        FaceEncoding,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reference_face",
    )
    file = models.ImageField(_("file"), upload_to=reference_face_uploadto)

    matches = models.ManyToManyField(FaceEncoding, related_name="matches")

    def match_photos(self):
        if not self.encoding:
            return

        matches = FaceEncoding.objects.filter(photo__isnull=False).extra(
            where=[face_recognition_distance_function(self.encoding.encoding)]
        )
        for encoding in self.matches.all():
            if encoding not in matches:
                self.matches.remove(encoding)
        for encoding in matches:
            self.matches.add(encoding)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert, force_update, using, update_fields)
        if self.encoding:
            self.match_photos()

    def __str__(self):
        return str(self.file)


class Album(models.Model):
    """Model for Album objects."""

    title = models.CharField(
        _("title"),
        blank=True,
        max_length=200,
        help_text=_("Leave empty to take over the title of the event"),
    )

    dirname = models.CharField(
        verbose_name=_("directory name"),
        max_length=200,
    )

    date = models.DateField(
        verbose_name=_("date"),
        blank=True,
        help_text=_("Leave empty to take over the date of the event"),
    )

    slug = models.SlugField(
        verbose_name=_("slug"),
        unique=True,
    )

    hidden = models.BooleanField(verbose_name=_("hidden"), default=False)

    new_album_notification = models.ForeignKey(
        ScheduledMessage, on_delete=models.deletion.SET_NULL, blank=True, null=True
    )

    event = models.ForeignKey(Event, on_delete=models.SET_NULL, blank=True, null=True)

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
        """Return cover of Album.

        If a cover is not set, return a random photo or None if there are no photos.
        """
        cover = None
        if self._cover is not None:
            return self._cover

        # Not prefetched because this should be rare and is a lot of data
        # `exists` is faster in theory, but requires everything to be fetched later anyways
        if self.photo_set.exists():
            random.seed(self.dirname)
            cover = random.choice(self.photo_set.all())
        return cover

    def __str__(self):
        """Get string representation of Album."""
        date = self.date.strftime("%Y-%m-%d")
        return f"{date} {self.title}"

    def get_absolute_url(self):
        """Get url of Album."""
        return reverse("photos:album", args=[str(self.slug)])

    def clean(self):
        super().clean()
        errors = {}

        if not self.title and not self.event:
            errors.update(
                {"title": _("This field is required if there is no event selected.")}
            )

        if not self.date and not self.event:
            errors.update(
                {"date": _("This field is required if there is no event selected.")}
            )

        if errors:
            raise ValidationError(errors)

    def save(self, **kwargs):
        """Save album and send appropriate notifications."""
        # dirname is only set for new objects, to avoid ever changing it
        if self.pk is None:
            self.dirname = self.slug

        if not self.title and self.event:
            self.title = self.event.title

        if not self.date:
            self.date = self.event.start.date()

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

            new_album_notification.title = "New album uploaded"
            new_album_notification.body = (
                f"A new photo album '{self.title}' has just been uploaded"
            )
            new_album_notification.category = Category.objects.get(key=Category.PHOTO)
            new_album_notification.url = f"{settings.BASE_URL}{self.get_absolute_url()}"
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

        super().save(**kwargs)

    @property
    def access_token(self):
        """Return access token for album."""
        return hashlib.sha256(
            f"{settings.SECRET_KEY}album{self.pk}".encode("utf-8")
        ).hexdigest()

    class Meta:
        """Meta class for Album."""

        ordering = ("-date", "title")
