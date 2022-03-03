"""Models for the promotion requests database tables."""
import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from tinymce.models import HTMLField

from events.models import Event


class PromotionChannel(models.Model):
    name = models.CharField(verbose_name=_("Channel name"), max_length=100)

    def __str__(self):
        return str(self.name)


class PromotionRequest(models.Model):
    created_at = models.DateTimeField(
        verbose_name=_("created at"), auto_now_add=True, null=False, blank=False
    )
    event = models.ForeignKey(
        Event, verbose_name=_("event"), on_delete=models.CASCADE, null=True, blank=True
    )
    publish_date = models.DateField(
        verbose_name=_("Publish date"),
        default=datetime.date.today,
        null=False,
        blank=False,
    )
    channel = models.ForeignKey(
        PromotionChannel,
        verbose_name=_("channel"),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    assigned_to = models.CharField(
        null=True,
        blank=True,
        max_length=50,
        verbose_name=_("Assigned to"),
    )

    NOT_STARTED = "not_started"
    STARTED = "started"
    FINISHED = "finished"
    PUBLISHED = "published"

    STATUS_TYPES = (
        (NOT_STARTED, _("Not started")),
        (STARTED, _("Started")),
        (FINISHED, _("Finished")),
        (PUBLISHED, _("Published")),
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_TYPES,
        verbose_name=_("status"),
        default=NOT_STARTED,
        null=False,
        blank=False,
    )
    drive_folder = models.URLField(
        verbose_name=_("drive folder"),
        null=True,
        blank=True,
        max_length=2000,  # This appears to be the max allowed url length
    )
    remarks = HTMLField(
        verbose_name=_("remarks"),
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.event:
            return _("Promotion request for ") + str(self.event)
        return _("Promotion request ") + str(self.pk)
    
    def clean(self):
        super().clean()
        errors = {}
        if self.publish_date is None:
            errors.update({"publish_date": _("Publish date cannot have an empty date field")})
        
        if errors:
            raise ValidationError(errors)

    def save(self, **kwargs):
        if not self.publish_date and self.event:
            self.publish_date = self.event.start.date()
        return super().save(kwargs)

    class Meta:
        verbose_name = _("Promotion request")
        verbose_name_plural = _("Promotion requests")
