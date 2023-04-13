import hashlib
import logging
import os
import random

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, IntegerField, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import AnnotationProperty
from thumbnails.fields import ImageField

from members.models import Member

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

    objects = QueryablePropertiesManager()

    album = models.ForeignKey(
        "Album", on_delete=models.CASCADE, verbose_name=_("album")
    )

    file = ImageField(
        _("file"),
        upload_to=photo_uploadto,
        pregenerated_sizes=["small", "medium", "large", "photo_medium", "photo_large"],
    )

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
        Coalesce(Count("likes"), Value(0), output_field=IntegerField())
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

        # Photos are created in order of their filename.
        ordering = ("pk",)


class Like(models.Model):
    photo = models.ForeignKey(
        Photo, null=False, blank=False, related_name="likes", on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        Member, null=True, blank=False, on_delete=models.SET_NULL
    )

    def __str__(self):
        return str(self.member) + " " + _("likes") + " " + str(self.photo)

    class Meta:
        unique_together = ["photo", "member"]


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

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
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
        return f"{self.date:%Y-%m-%d} {self.title}"

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
