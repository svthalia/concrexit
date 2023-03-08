"""The models defined by the announcement package."""
from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)
from django.db import models
from django.db.models import CharField, Manager, Q
from django.db.models.functions import Now
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tinymce.models import HTMLField

from thaliawebsite.storage.backend import get_public_storage


class VisibleObjectManager(Manager):
    """Get all active members, i.e. who have a committee membership."""

    def get_queryset(self):
        """Select all visible items."""
        return (
            super()
            .get_queryset()
            .filter(
                (Q(until__isnull=True) | Q(until__gt=Now()))
                & (Q(since__isnull=True) | Q(since__lte=Now()))
                & ~(Q(since__isnull=True) & Q(until__isnull=True))
            )
        )


class Announcement(models.Model):
    """Describes an announcement."""

    objects = models.Manager()
    visible_objects = VisibleObjectManager()

    content = HTMLField(
        verbose_name=_("Content"),
        help_text=_("The content of the announcement; what text to display."),
        blank=False,
        max_length=500,
    )

    since = models.DateTimeField(
        verbose_name=_("Display since"),
        help_text=_("Hide this announcement before this time."),
        default=timezone.now,
    )

    until = models.DateTimeField(
        verbose_name=_("Display until"),
        help_text=_("Hide this announcement after this time."),
        blank=True,
        null=True,
    )

    icon = models.CharField(
        verbose_name=_("Font Awesome icon"),
        help_text=_("Font Awesome abbreviation for icon to use."),
        max_length=150,
        default="bullhorn",
    )

    closeable = models.BooleanField(default=True)

    class Meta:
        ordering = ("-since",)

    def __str__(self):
        return str(self.content)

    @property
    def is_visible(self):
        """Is this announcement currently visible."""
        return (
            (self.until is None or self.until > timezone.now())
            and (self.since is None or self.since <= timezone.now())
            and not (self.since is None and self.until is None)
        )


class FrontpageArticle(models.Model):
    """Front page articles."""

    objects = models.Manager()
    visible_objects = VisibleObjectManager()

    title = models.CharField(
        verbose_name=_("Title"),
        help_text=_("The title of the article; what goes in the header"),
        blank=False,
        max_length=80,
    )

    content = HTMLField(
        verbose_name=_("Content"),
        help_text=_("The content of the article; what text to display."),
        blank=False,
        max_length=5000,
    )

    since = models.DateTimeField(
        verbose_name=_("Display since"),
        help_text=_("Hide this article before this time."),
        default=timezone.now,
    )

    until = models.DateTimeField(
        verbose_name=_("Display until"),
        help_text=_("Hide this article after this time."),
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("-since",)

    def __str__(self):
        return str(self.title)

    @property
    def is_visible(self):
        """Is this announcement currently visible."""
        return (
            (self.until is None or self.until > timezone.now())
            and (self.since is None or self.since <= timezone.now())
            and not (self.since is None and self.until is None)
        )


def validate_image(value):
    return FileExtensionValidator(
        allowed_extensions=[*get_available_image_extensions(), "svg"]
    )(value)


class Slide(models.Model):
    """Describes an announcement."""

    objects = models.Manager()
    visible_objects = VisibleObjectManager()

    title = CharField(
        verbose_name=_("Title"),
        help_text=_("The title of the slide; just for the admin."),
        blank=False,
        max_length=100,
    )

    content = models.FileField(
        verbose_name=_("Content"),
        help_text=_("The content of the slide; what image to display."),
        blank=False,
        upload_to="announcements/slides/",
        storage=get_public_storage,
        validators=[validate_image],
    )

    since = models.DateTimeField(
        verbose_name=_("Display since"),
        help_text=_(
            "Hide this slide before this time. When all date- and "
            "time-fields are left blank, the slide won't "
            "be visible. It will, however, be visible on an event-page "
            "if it's linked to an event."
        ),
        default=timezone.now,
        blank=True,
        null=True,
    )

    until = models.DateTimeField(
        verbose_name=_("Display until"),
        help_text=_("Hide this slide after this time."),
        blank=True,
        null=True,
    )

    order = models.PositiveIntegerField(
        verbose_name=_("Order"),
        help_text=_("Approximately where this slide should appear in the order"),
        default=0,
    )

    members_only = models.BooleanField(
        verbose_name=_("Display only for authenticated members"), default=False
    )

    custom_url = models.URLField(
        verbose_name=_("Link"),
        help_text=_(
            "Place the user is taken to when clicking the slide."
            "If left blank, will default to the linked event, if any."
        ),
        blank=True,
        null=True,
    )

    url_blank = models.BooleanField(
        verbose_name=_("Link outside thalia.nu"),
        help_text=_("Clicking the slide will open a new tab"),
        default=False,
    )

    event = models.OneToOneField(
        "events.Event",
        related_name="slide",
        null=True,
        blank=True,
        help_text="This event's header image will be changed to this slide.",
        on_delete=models.deletion.SET_NULL,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.content:
            self._orig_image = self.content.name
        else:
            self._orig_image = None

    def delete(self, using=None, keep_parents=False):
        if self.content.name:
            self.content.delete()
        return super().delete(using, keep_parents)

    def save(self, **kwargs):
        super().save(**kwargs)
        storage = self.content.storage

        if self._orig_image and self._orig_image != self.content.name:
            storage.delete(self._orig_image)
            self._orig_image = None

    class Meta:
        ordering = ("-since",)

    @property
    def is_visible(self):
        """Is this slide currently visible."""
        return (
            (self.until is None or self.until > timezone.now())
            and (self.since is None or self.since <= timezone.now())
            and not (self.since is None and self.until is None)
        )

    @property
    def url(self):
        if self.custom_url:
            return self.custom_url
        if self.event:
            return self.event.get_absolute_url()
        return None

    def __str__(self):
        return str(self.title)
