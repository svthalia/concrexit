"""Models for the promotion requests database tables."""
from django.db import models
import datetime

from django.db.models.deletion import CASCADE

from events.models import Event
from members.models.member import Member
from promotion.emails import notify_new_request


class PromotionChannel(models.Model):
    name = models.CharField(verbose_name = "Channel name", max_length=100)

    def __str__(self):
        return str(self.name)


class PromotionRequest(models.Model):
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE
    )
    publish_date = models.DateField(
        blank=True, 
        verbose_name="Publish date", 
        default=datetime.date.today
    )
    channel = models.ForeignKey(
        PromotionChannel,
        on_delete=models.CASCADE,
        default = "0"
    )
    assigned_to = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        verbose_name="Assigned to",
        default = "0"
    )
    status = models.CharField(
        max_length = 40,
        choices = [("0", "Not started"), ("1", "Started"), ("2", "Finished"), ("3", "Published")],
        default = "0"
    )
    drive_folder = models.CharField(
        max_length = 200,
        default = ""
    )

    def __str__(self):
        return "Promotion request for " + str(self.event)

    def save(self, **kwargs):
        if not self.publish_date:
            self.publish_date = self.event.start.date()
        notify_new_request(self)

        return super().save(kwargs)
