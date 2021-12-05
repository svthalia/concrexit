from django.db import models
from django.utils.translation import gettext_lazy as _

from events.models import EVENT_CATEGORIES


class ExternalEvent(models.Model):
    """Model describing an external event."""

    organiser = models.CharField(max_length=255)

    category = models.CharField(
        max_length=40,
        choices=EVENT_CATEGORIES,
        verbose_name=_("category"),
        help_text=_(
            "Alumni: Events organised for alumni, "
            "Education: Education focused events, "
            "Career: Career focused events, "
            "Leisure: borrels, parties, game activities etc., "
            "Association Affairs: general meetings or "
            "any other board related events, "
            "Other: anything else."
        ),
    )

    title = models.CharField(_("title"), max_length=100)

    description = models.TextField(_("description"))

    location = models.CharField(
        _("location"),
        max_length=255,
    )

    start = models.DateTimeField(_("start time"))

    end = models.DateTimeField(_("end time"))

    url = models.URLField(_("website"))

    published = models.BooleanField(_("published"), default=False)

    def __str__(self):
        """Return the event title."""
        return str(self.title)
