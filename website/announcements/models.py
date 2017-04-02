from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from utils.translation import ModelTranslateMeta, MultilingualField


class Announcement(models.Model, metaclass=ModelTranslateMeta):
    content = MultilingualField(
        models.CharField,
        verbose_name=_('Content'),
        help_text=_('The content of the announcement; what text to display.'),
        blank=False,
        max_length=500,
    )

    since = models.DateTimeField(
        verbose_name=_('Display since'),
        help_text=_("Hide this announcement before this time."),
        default=timezone.now,
    )

    until = models.DateTimeField(
        verbose_name=_('Display until'),
        help_text=_("Hide this announcement after this time."),
        blank=True,
        null=True,
    )

    icon = models.CharField(
        verbose_name=_('Font Awesome icon'),
        help_text=_("Font Awesome abbreviation for icon to use."),
        max_length=150,
        default='bullhorn',
    )

    closeable = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ('-since', )

    def __str__(self):
        return self.content

    @property
    def is_visible(self):
        """Is this announcement currently visible"""
        return ((self.until is None or self.until > timezone.now()) and
                (self.since is None or self.since <= timezone.now()))
