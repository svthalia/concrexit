"""Models for the promotion requests database tables."""
from django.db import models
import datetime

from django.db.models.deletion import CASCADE
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from events.models import Event
from members.models.member import Member
from promotion.emails import notify_new_request


class PromotionChannel(models.Model):
    name = models.CharField(
        verbose_name = _("Channel name"), 
        max_length=100
    )

    def __str__(self):
        return str(self.name)


class PromotionRequest(models.Model):
    event = models.ForeignKey(
        Event,
        verbose_name = _("event"),
        on_delete=models.CASCADE,
        null = True,
    )
    publish_date = models.DateField( 
        verbose_name=_("Publish date"), 
        default=datetime.date.today
    )
    channel = models.ForeignKey(
        PromotionChannel,
        verbose_name = _("channel"),
        on_delete=models.CASCADE
    )
    assigned_to = models.CharField(
        max_length = 40,
        verbose_name=_("Assigned to"),
        default = ""
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
        max_length = 40,
        choices = STATUS_TYPES,
        verbose_name = _("status"),
        default = NOT_STARTED,
    )
    drive_folder = models.URLField(
        max_length = 200,
        default = ""
    )
    remarks = HTMLField(("remarks"),)
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return _("Promotion request for ") + str(self.event)

    def save(self, **kwargs):
        if not self.publish_date:
            self.publish_date = self.event.start.date()
        notify_new_request(self)

        return super().save(kwargs)
    
    class Meta:
        verbose_name = _("Promotion request")
        verbose_name_plural = _("Promotion requests")
